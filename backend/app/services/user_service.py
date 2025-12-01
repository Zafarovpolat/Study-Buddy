from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import Optional
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
            subscription_tier=SubscriptionTier.FREE
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
    ) -> tuple[User, bool]:
        """Получить или создать пользователя. Возвращает (user, is_new)"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            # Обновляем username если изменился
            if username and user.telegram_username != username:
                user.telegram_username = username
                await self.db.commit()
            return user, False
        
        user = await self.create_user(telegram_id, username, first_name)
        return user, True
    
    async def check_rate_limit(self, user: User) -> tuple[bool, int]:
        """
        Проверка лимита запросов.
        Возвращает (can_proceed, remaining_requests)
        """
        if user.subscription_tier != SubscriptionTier.FREE:
            return True, -1  # Unlimited
        
        today = date.today()
        
        # Сброс счётчика если новый день
        if user.last_request_date is None or user.last_request_date.date() < today:
            user.daily_requests_count = 0
            user.last_request_date = datetime.now()
            await self.db.commit()
        
        remaining = settings.FREE_DAILY_LIMIT - user.daily_requests_count
        can_proceed = remaining > 0
        
        return can_proceed, max(0, remaining)
    
    async def increment_request_count(self, user: User) -> None:
        """Увеличить счётчик запросов"""
        user.daily_requests_count += 1
        user.last_request_date = datetime.now()
        await self.db.commit()
    
    async def upgrade_subscription(self, user: User, tier: SubscriptionTier) -> User:
        """Обновить подписку пользователя"""
        user.subscription_tier = tier
        await self.db.commit()
        await self.db.refresh(user)
        return user