# backend/app/services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio

scheduler = AsyncIOScheduler()


async def send_streak_reminders():
    """Отправка напоминаний о streak (запускается в 10:00 и 19:00)"""
    from app.models import AsyncSessionLocal
    from app.services.notification_service import NotificationService
    
    print(f"🔔 Running streak reminders at {datetime.now()}")
    
    try:
        from app.main import bot_app
        if not bot_app:
            print("⚠️ Bot not available for notifications")
            return
        
        async with AsyncSessionLocal() as db:
            service = NotificationService(db)
            users = await service.get_users_for_streak_reminder()
            
            print(f"📨 Sending reminders to {len(users)} users")
            
            for user in users:
                await service.send_streak_reminder(user, bot_app.bot)
            
            print(f"✅ Streak reminders sent")
    
    except Exception as e:
        print(f"❌ Streak reminder error: {e}")
        import traceback
        traceback.print_exc()


async def keep_alive_ping():
    """Пингуем сами себя чтобы Render не засыпал"""
    from app.core.config import settings
    
    if not settings.FRONTEND_URL:
        print("⚠️ FRONTEND_URL not set, skip keep-alive")
        return
    
    url = f"{settings.FRONTEND_URL}/api/health"
    
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                print(f"🏓 Keep-alive ping: {resp.status}")
    except Exception as e:
        print(f"⚠️ Keep-alive failed: {e}")


def setup_scheduler():
    """Настройка планировщика"""
    
    # Напоминание утром (10:00 UTC+5 = 05:00 UTC)
    scheduler.add_job(
        lambda: asyncio.create_task(send_streak_reminders()),
        CronTrigger(hour=5, minute=0),
        id="streak_reminder_morning",
        replace_existing=True
    )
    
    # Напоминание вечером (19:00 UTC+5 = 14:00 UTC)
    scheduler.add_job(
        lambda: asyncio.create_task(send_streak_reminders()),
        CronTrigger(hour=14, minute=0),
        id="streak_reminder_evening",
        replace_existing=True
    )
    
    # Keep-alive каждые 10 минут — Render не засыпает!
    scheduler.add_job(
        lambda: asyncio.create_task(keep_alive_ping()),
        IntervalTrigger(minutes=10),
        id="keep_alive",
        replace_existing=True
    )
    
    print("📅 Scheduler configured:")
    print("   - Streak reminders: 10:00 & 19:00 (UTC+5)")
    print("   - Keep-alive ping: every 10 minutes")


def start_scheduler():
    """Запуск планировщика"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        print("✅ Scheduler started")


def stop_scheduler():
    """Остановка планировщика"""
    if scheduler.running:
        scheduler.shutdown()
        print("⏹️ Scheduler stopped")