# backend/app/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from uuid import UUID

from app.models import User, SubscriptionTier, TIER_LIMITS


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
            daily_requests=0,
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
        # Pro/SOS без лимитов
        if user.is_pro:
            return True, -1
        
        today = date.today()
        
        # Сбрасываем счётчик если новый день
        if user.last_request_date is None or user.last_request_date.date() < today:
            user.daily_requests = 0
            user.last_request_date = datetime.now()
            await self.db.commit()
        
        # Получаем лимит из тарифа (3 для Free)
        daily_limit = user.daily_limit
        remaining = daily_limit - (user.daily_requests or 0)
        
        return remaining > 0, max(0, remaining)
    
    async def increment_request_count(self, user: User) -> None:
        """Увеличить счётчик запросов и обновить streak"""
        user.daily_requests = (user.daily_requests or 0) + 1
        user.last_request_date = datetime.now()
        
        await self._update_streak(user)
        await self.db.commit()
    
    async def _update_streak(self, user: User) -> None:
        """Обновить streak пользователя"""
        today = date.today()
        
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
            pass
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
    
    async def get_limits_info(self, user: User) -> dict:
        """Получить информацию о лимитах пользователя"""
        today = date.today()
        
        # Сбрасываем если новый день
        if user.last_request_date is None or user.last_request_date.date() < today:
            used_today = 0
        else:
            used_today = user.daily_requests or 0
        
        daily_limit = user.daily_limit
        remaining = max(0, daily_limit - used_today) if daily_limit < 999999 else -1
        
        # Информация о подписке
        subscription_info = {
            "tier": user.effective_tier,
            "is_pro": user.is_pro,
            "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        }
        
        # Доступные функции
        features = user.tier_limits.get("features", [])
        
        return {
            "daily_limit": daily_limit if daily_limit < 999999 else None,
            "used_today": used_today,
            "remaining_today": remaining,
            "subscription": subscription_info,
            "limits": {
                "max_groups": user.max_groups,
                "max_members_per_group": user.max_members_per_group if user.max_members_per_group < 999999 else None,
                "max_materials_per_group": user.max_materials_per_group if user.max_materials_per_group < 999999 else None,
                "audio_minutes": user.audio_minutes_limit,
            },
            "features": features
        }
    
    async def upgrade_subscription(
        self, 
        user: User, 
        tier: str,
        duration_days: Optional[int] = None
    ) -> User:
        """Обновить подписку"""
        user.subscription_tier = tier
        
        if duration_days:
            user.subscription_expires_at = datetime.utcnow() + timedelta(days=duration_days)
        elif tier == SubscriptionTier.SOS:
            # SOS на 24 часа
            user.subscription_expires_at = datetime.utcnow() + timedelta(hours=24)
        else:
            user.subscription_expires_at = None  # Бессрочно (или настроить)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def activate_sos(self, user: User) -> User:
        """Активировать SOS тариф на 24 часа"""
        return await self.upgrade_subscription(user, SubscriptionTier.SOS, duration_days=None)

    async def update_profile(
        self,
        user: User,
        field_of_study: Optional[str] = None,
        region: Optional[str] = None
    ) -> User:
        """Обновить профиль пользователя (Lecto 2.0)"""
        if field_of_study:
            user.field_of_study = field_of_study
        if region:
            user.region = region
            
        user.onboarding_completed = True
        
        await self.db.commit()
        await self.db.refresh(user)
        return user