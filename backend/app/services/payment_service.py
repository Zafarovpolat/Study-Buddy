# backend/app/services/payment_service.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import User, SubscriptionTier


# Цены в Telegram Stars
PRICES = {
    "pro_monthly": 150,      # 150 Stars = ~$2.99
    "pro_yearly": 1200,      # 1200 Stars = ~$23.99 (скидка 33%)
}


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_invoice_data(self, plan: str = "pro_monthly") -> dict:
        """Создать данные для invoice"""
        if plan == "pro_monthly":
            return {
                "title": "Pro подписка (1 месяц)",
                "description": "Безлимитные материалы, приоритетная обработка",
                "payload": "pro_monthly",
                "currency": "XTR",  # Telegram Stars
                "prices": [{"label": "Pro 1 мес", "amount": PRICES["pro_monthly"]}],
            }
        elif plan == "pro_yearly":
            return {
                "title": "Pro подписка (1 год)",
                "description": "Безлимит на год со скидкой 33%!",
                "payload": "pro_yearly",
                "currency": "XTR",
                "prices": [{"label": "Pro 1 год", "amount": PRICES["pro_yearly"]}],
            }
        else:
            raise ValueError(f"Unknown plan: {plan}")
    
    async def process_successful_payment(
        self,
        user: User,
        payload: str,
        telegram_payment_charge_id: str
    ) -> User:
        """Обработать успешный платёж"""
        
        # Определяем срок подписки
        if payload == "pro_monthly":
            duration = timedelta(days=30)
        elif payload == "pro_yearly":
            duration = timedelta(days=365)
        else:
            duration = timedelta(days=30)
        
        # Если уже есть подписка — продлеваем
        if user.subscription_expires_at and user.subscription_expires_at > datetime.now():
            new_expires = user.subscription_expires_at + duration
        else:
            new_expires = datetime.now() + duration
        
        # Обновляем пользователя
        user.subscription_tier = SubscriptionTier.PRO
        user.subscription_expires_at = new_expires
        user.telegram_payment_charge_id = telegram_payment_charge_id
        
        await self.db.commit()
        await self.db.refresh(user)
        
        print(f"✅ User {user.telegram_id} upgraded to PRO until {new_expires}")
        
        return user
    
    async def check_subscription_status(self, user: User) -> dict:
        """Проверить статус подписки"""
        if user.subscription_tier == SubscriptionTier.FREE:
            return {
                "is_pro": False,
                "tier": "free",
                "expires_at": None,
                "days_left": 0
            }
        
        if user.subscription_expires_at:
            now = datetime.now()
            if user.subscription_expires_at > now:
                days_left = (user.subscription_expires_at - now).days
                return {
                    "is_pro": True,
                    "tier": user.subscription_tier.value,
                    "expires_at": user.subscription_expires_at.isoformat(),
                    "days_left": days_left
                }
            else:
                # Подписка истекла
                user.subscription_tier = SubscriptionTier.FREE
                await self.db.commit()
                return {
                    "is_pro": False,
                    "tier": "free",
                    "expires_at": None,
                    "days_left": 0,
                    "expired": True
                }
        
        return {
            "is_pro": True,
            "tier": user.subscription_tier.value,
            "expires_at": None,
            "days_left": -1  # Бессрочно
        }