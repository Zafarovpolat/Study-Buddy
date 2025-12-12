# backend/app/services/user_service.py
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
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
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
        user = User(
            telegram_id=telegram_id,
            telegram_username=username,
            first_name=first_name,
            subscription_tier=SubscriptionTier.FREE,
            daily_requests=0,  # ← Правильное имя!
            current_streak=0,
            longest_streak=0,
            referral_count=0,
            referral_pro_granted=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        print(f"✅ Created new user: {telegram_id}")
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Tuple[User, bool]:
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
    
    async def check_rate_limit(self, user: User) -> Tuple[bool, int]:
        """Проверка лимита запросов"""
        # Pro без лимитов
        if user.is_pro:
            return True, -1
        
        # Проверяем tier как строку!
        if user.subscription_tier != SubscriptionTier.FREE:
            return True, -1
        
        today = date.today()
        
        # Сбрасываем счётчик если новый день
        if user.last_request_date is None or user.last_request_date.date() < today:
            user.daily_requests = 0  # ← Правильное имя!
            user.last_request_date = datetime.now()
            await self.db.commit()
        
        remaining = settings.FREE_DAILY_LIMIT - (user.daily_requests or 0)  # ← Правильное имя!
        return remaining > 0, max(0, remaining)
    
    async def increment_request_count(self, user: User) -> None:
        """Увеличить счётчик запросов и обновить streak"""
        user.daily_requests = (user.daily_requests or 0) + 1  # ← Правильное имя!
        user.last_request_date = datetime.now()
        
        await self._update_streak(user)
        await self.db.commit()
    
    async def _update_streak(self, user: User) -> None:
        """Обновить streak пользователя"""
        today = date.today()
        
        # last_activity_date может быть datetime или date
        last_date = None
        if user.last_activity_date:
            if hasattr(user.last_activity_date, 'date'):
                last_date = user.last_activity_date.date()
            else:
                last_date = user.last_activity_date
        
        if last_date is None:
            user.current_streak = 1
            user.longest_streak = 1
        elif last_date == today:
            pass  # Уже был сегодня
        elif last_date == today - timedelta(days=1):
            user.current_streak = (user.current_streak or 0) + 1
            if user.current_streak > (user.longest_streak or 0):
                user.longest_streak = user.current_streak
        else:
            user.current_streak = 1
        
        user.last_activity_date = datetime.now()
    
    async def get_streak_info(self, user: User) -> dict:
        """Получить информацию о streak"""
        today = date.today()
        
        last_date = None
        if user.last_activity_date:
            if hasattr(user.last_activity_date, 'date'):
                last_date = user.last_activity_date.date()
            else:
                last_date = user.last_activity_date
        
        if last_date and last_date < today - timedelta(days=1):
            current = 0
        else:
            current = user.current_streak or 0
        
        return {
            "current_streak": current,
            "longest_streak": user.longest_streak or 0,
            "last_activity": user.last_activity_date.isoformat() if user.last_activity_date else None,
            "is_active_today": last_date == today if last_date else False
        }
    
    async def upgrade_subscription(self, user: User, tier: str) -> User:
        """Обновить подписку"""
        user.subscription_tier = tier
        await self.db.commit()
        await self.db.refresh(user)
        return user