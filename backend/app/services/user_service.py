# backend/app/services/user_service.py - ЗАМЕНИ ПОЛНОСТЬЮ
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from uuid import UUID

from app.models import User, SubscriptionTier
from app.core.config import settings


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self, 
        telegram_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=first_name,
            subscription_tier=SubscriptionTier.FREE,
            current_streak=0,
            longest_streak=0
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Tuple[User, bool]:
        """Получить или создать пользователя"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            if username and user.telegram_username != username:
                user.telegram_username = username
                await self.db.commit()
            return user, False
        
        try:
            user = await self.create_user(telegram_id, username, first_name)
            return user, True
        except Exception:
            await self.db.rollback()
            user = await self.get_by_telegram_id(telegram_id)
            if user:
                return user, False
            raise
    
    # backend/app/services/user_service.py - ОБНОВИ метод check_rate_limit

    async def check_rate_limit(self, user: User) -> Tuple[bool, int]:
        """Проверка лимита запросов"""
        # Pro юзеры без лимитов
        if user.is_pro:
            return True, -1
        
        if user.subscription_tier != SubscriptionTier.FREE:
            return True, -1
        
        today = date.today()
        
        if user.last_request_date is None or user.last_request_date.date() < today:
            user.daily_requests_count = 0
            user.last_request_date = datetime.now()
            await self.db.commit()
        
        remaining = settings.FREE_DAILY_LIMIT - user.daily_requests_count
        return remaining > 0, max(0, remaining)
    
    async def increment_request_count(self, user: User) -> None:
        """Увеличить счётчик запросов и обновить streak"""
        user.daily_requests_count += 1
        user.last_request_date = datetime.now()
        
        # Обновляем streak
        await self._update_streak(user)
        
        await self.db.commit()
    
    async def _update_streak(self, user: User) -> None:
        """Обновить streak пользователя"""
        today = date.today()
        
        if user.last_activity_date is None:
            # Первая активность
            user.current_streak = 1
            user.longest_streak = 1
        elif user.last_activity_date == today:
            # Уже был сегодня - ничего не меняем
            pass
        elif user.last_activity_date == today - timedelta(days=1):
            # Был вчера - продолжаем streak
            user.current_streak += 1
            if user.current_streak > user.longest_streak:
                user.longest_streak = user.current_streak
        else:
            # Пропустил день(и) - сбрасываем streak
            user.current_streak = 1
        
        user.last_activity_date = today
    
    async def get_streak_info(self, user: User) -> dict:
        """Получить информацию о streak"""
        today = date.today()
        
        # Проверяем не сбросился ли streak
        if user.last_activity_date and user.last_activity_date < today - timedelta(days=1):
            # Streak сбросился, но не обновляем БД пока нет активности
            current = 0
        else:
            current = user.current_streak or 0
        
        return {
            "current_streak": current,
            "longest_streak": user.longest_streak or 0,
            "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None,
            "is_active_today": user.last_activity_date == today if user.last_activity_date else False
        }
    
    async def upgrade_subscription(self, user: User, tier: SubscriptionTier) -> User:
        """Обновить подписку"""
        user.subscription_tier = tier
        await self.db.commit()
        await self.db.refresh(user)
        return user