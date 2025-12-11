# backend/app/services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_streak_reminders():
    """Отправка напоминаний о streak (запускается в 10:00 и 19:00)"""
    logger.info(f"🔔 Running streak reminders at {datetime.now()}")
    
    try:
        from app.main import bot_app
        if not bot_app:
            logger.warning("⚠️ Bot not available for notifications")
            return
        
        from app.models.base import AsyncSessionLocal
        from app.services.notification_service import NotificationService
        
        async with AsyncSessionLocal() as db:
            service = NotificationService(db)
            users = await service.get_users_for_streak_reminder()
            
            logger.info(f"📨 Sending reminders to {len(users)} users")
            
            for user in users:
                try:
                    await service.send_streak_reminder(user, bot_app.bot)
                except Exception as e:
                    logger.error(f"Failed to send to {user.telegram_id}: {e}")
            
            logger.info(f"✅ Streak reminders sent")
    
    except Exception as e:
        logger.error(f"❌ Streak reminder error: {e}")
        import traceback
        traceback.print_exc()


async def keep_alive_ping():
    """Пингуем сами себя чтобы Render не засыпал"""
    from app.core.config import settings
    
    if not settings.FRONTEND_URL:
        logger.warning("⚠️ FRONTEND_URL not set, skip keep-alive")
        return
    
    url = f"{settings.FRONTEND_URL}/api/health"
    
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                logger.info(f"🏓 Keep-alive ping: {resp.status}")
    except Exception as e:
        logger.warning(f"⚠️ Keep-alive failed: {e}")


def setup_scheduler():
    """Настройка планировщика"""
    
    # Напоминание утром (10:00 UTC+5 = 05:00 UTC)
    # AsyncIOScheduler сам вызывает async функции!
    scheduler.add_job(
        send_streak_reminders,  # ← Напрямую async функция, БЕЗ lambda!
        CronTrigger(hour=5, minute=0),
        id="streak_reminder_morning",
        replace_existing=True
    )
    
    # Напоминание вечером (19:00 UTC+5 = 14:00 UTC)
    scheduler.add_job(
        send_streak_reminders,  # ← Напрямую async функция
        CronTrigger(hour=14, minute=0),
        id="streak_reminder_evening",
        replace_existing=True
    )
    
    # Keep-alive каждые 10 минут
    scheduler.add_job(
        keep_alive_ping,  # ← Напрямую async функция
        IntervalTrigger(minutes=10),
        id="keep_alive",
        replace_existing=True
    )
    
    logger.info("📅 Scheduler configured:")
    logger.info("   - Streak reminders: 10:00 & 19:00 (UTC+5)")
    logger.info("   - Keep-alive ping: every 10 minutes")


def start_scheduler():
    """Запуск планировщика"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info("✅ Scheduler started")


def stop_scheduler():
    """Остановка планировщика"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("⏹️ Scheduler stopped")