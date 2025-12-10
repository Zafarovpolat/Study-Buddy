# backend/app/services/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

scheduler = AsyncIOScheduler()


async def send_streak_reminders():
    """Отправка напоминаний о streak (запускается в 10:00 и 19:00)"""
    from app.models import AsyncSessionLocal
    from app.services.notification_service import NotificationService
    
    print(f"🔔 Running streak reminders at {datetime.now()}")
    
    try:
        # Получаем бота из глобального состояния
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


def setup_scheduler():
    """Настройка планировщика"""
    
    # Напоминание утром (10:00 UTC+5 = 05:00 UTC)
    scheduler.add_job(
        send_streak_reminders,
        CronTrigger(hour=5, minute=0),  # 10:00 по Ташкенту
        id="streak_reminder_morning",
        replace_existing=True
    )
    
    # Напоминание вечером (19:00 UTC+5 = 14:00 UTC)
    scheduler.add_job(
        send_streak_reminders,
        CronTrigger(hour=14, minute=0),  # 19:00 по Ташкенту
        id="streak_reminder_evening",
        replace_existing=True
    )
    
    print("📅 Scheduler configured:")
    print("   - Streak reminders: 10:00 & 19:00 (UTC+5)")


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