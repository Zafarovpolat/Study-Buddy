# backend/app/services/notification_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from app.models import User
from app.core.config import settings


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_users_for_streak_reminder(self) -> list[User]:
        """Получить пользователей, которым нужно напомнить о streak"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Пользователи, которые:
        # 1. Были активны вчера (есть streak)
        # 2. Не были активны сегодня
        # 3. Имеют streak > 0
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.last_activity_date == yesterday,
                    User.current_streak > 0
                )
            )
        )
        return list(result.scalars().all())
    
    async def send_streak_reminder(self, user: User, bot) -> bool:
        """Отправить напоминание о streak"""
        try:
            message = (
                f"🔥 Привет, {user.first_name or 'друг'}!\n\n"
                f"Твой streak: **{user.current_streak} дней**\n"
                f"Не забудь поучиться сегодня, чтобы не потерять прогресс!\n\n"
                f"📚 Открой приложение и загрузи материал"
            )
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to send reminder to {user.telegram_id}: {e}")
            return False
    
    async def send_group_material_notification(
        self, 
        group_name: str,
        material_title: str,
        uploader_name: str,
        member_telegram_ids: list[int],
        exclude_user_id: int,
        bot
    ) -> int:
        """Уведомить участников группы о новом материале"""
        sent_count = 0
        
        message = (
            f"📚 Новый материал в группе **{group_name}**!\n\n"
            f"📄 {material_title}\n"
            f"👤 Добавил: {uploader_name}\n\n"
            f"Открой приложение, чтобы посмотреть"
        )
        
        for telegram_id in member_telegram_ids:
            if telegram_id == exclude_user_id:
                continue
            
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception as e:
                print(f"❌ Failed to notify {telegram_id}: {e}")
        
        return sent_count