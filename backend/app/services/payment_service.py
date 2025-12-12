# backend/app/services/payment_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models import User, SubscriptionTier


# Цены в Telegram Stars
# 1 Star ≈ $0.02-0.03
PRICES = {
    "pro_monthly": 250,      # ~$4.99 = ~65,000 UZS
    "pro_yearly": 2000,      # ~$39.99 (скидка 33%)
    "sos_24h": 50,           # ~$0.99 = ~12,000 UZS
}


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_invoice_data(self, plan: str = "pro_monthly") -> dict:
        """Создать данные для invoice"""
        plans = {
            "pro_monthly": {
                "title": "Lecto Pro — 1 месяц",
                "description": "✨ Безлимитные генерации\n🎧 Audio-Dialog\n💬 AI-Debate\n📊 Презентации\n🔍 Vector Search",
                "payload": "pro_monthly",
                "currency": "XTR",
                "prices": [{"label": "Pro 1 мес", "amount": PRICES["pro_monthly"]}],
            },
            "pro_yearly": {
                "title": "Lecto Pro — 1 год",
                "description": "🔥 Скидка 33%!\n✨ Безлимитные генерации\n🎧 Audio-Dialog\n💬 AI-Debate\n📊 Презентации\n🔍 Vector Search",
                "payload": "pro_yearly",
                "currency": "XTR",
                "prices": [{"label": "Pro 1 год", "amount": PRICES["pro_yearly"]}],
            },
            "sos_24h": {
                "title": "Lecto SOS — 24 часа",
                "description": "🔥 Экзамен завтра?\n✨ Безлимит на 24 часа\n🎧 Audio-Dialog\n💬 AI-Debate\n📊 Презентации",
                "payload": "sos_24h",
                "currency": "XTR",
                "prices": [{"label": "SOS 24ч", "amount": PRICES["sos_24h"]}],
            },
        }
        
        if plan not in plans:
            raise ValueError(f"Unknown plan: {plan}")
        
        return plans[plan]
    
    async def process_successful_payment(
        self,
        user: User,
        payload: str,
        telegram_payment_charge_id: str
    ) -> User:
        """Обработать успешный платёж"""
        now = datetime.utcnow()
        
        # Определяем tier и срок подписки
        if payload == "pro_monthly":
            tier = SubscriptionTier.PRO
            duration = timedelta(days=30)
        elif payload == "pro_yearly":
            tier = SubscriptionTier.PRO
            duration = timedelta(days=365)
        elif payload == "sos_24h":
            tier = SubscriptionTier.SOS
            duration = timedelta(hours=24)
        else:
            tier = SubscriptionTier.PRO
            duration = timedelta(days=30)
        
        # Если уже есть активная подписка — продлеваем
        if user.subscription_expires_at and user.subscription_expires_at > now:
            # Для SOS не продлеваем Pro, а заменяем
            if payload == "sos_24h":
                new_expires = now + duration
            else:
                new_expires = user.subscription_expires_at + duration
        else:
            new_expires = now + duration
        
        # Обновляем пользователя
        user.subscription_tier = tier
        user.subscription_expires_at = new_expires
        
        await self.db.commit()
        await self.db.refresh(user)
        
        print(f"✅ User {user.telegram_id} upgraded to {tier.value} until {new_expires}")
        
        return user
    
    async def check_subscription_status(self, user: User) -> dict:
        """Проверить статус подписки"""
        now = datetime.utcnow()
        
        if user.subscription_tier == SubscriptionTier.FREE:
            return {
                "is_pro": False,
                "tier": "free",
                "expires_at": None,
                "days_left": 0,
                "hours_left": 0,
                "features": self._get_features(False)
            }
        
        if user.subscription_expires_at:
            if user.subscription_expires_at > now:
                time_left = user.subscription_expires_at - now
                days_left = time_left.days
                hours_left = time_left.seconds // 3600
                
                return {
                    "is_pro": True,
                    "tier": user.subscription_tier,
                    "expires_at": user.subscription_expires_at.isoformat(),
                    "days_left": days_left,
                    "hours_left": hours_left if days_left == 0 else 0,
                    "features": self._get_features(True)
                }
            else:
                # Подписка истекла
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_expires_at = None
                await self.db.commit()
                
                return {
                    "is_pro": False,
                    "tier": "free",
                    "expires_at": None,
                    "days_left": 0,
                    "hours_left": 0,
                    "expired": True,
                    "features": self._get_features(False)
                }
        
        # Бессрочный Pro (за рефералов)
        return {
            "is_pro": True,
            "tier": user.subscription_tier,
            "expires_at": None,
            "days_left": -1,
            "hours_left": -1,
            "features": self._get_features(True)
        }
    
    def _get_features(self, is_pro: bool) -> dict:
        """Список доступных функций"""
        return {
            "smart_notes": True,
            "quiz": True,
            "flashcards": True,
            "glossary": True,
            "tldr": True,
            "daily_limit": 999999 if is_pro else 5,
            # Pro features
            "audio_dialog": is_pro,
            "ai_debate": is_pro,
            "presentation": is_pro,
            "vector_search": is_pro,
        }
    
    async def grant_referral_bonus(self, user: User) -> User:
        """Выдать бонус за рефералов (30 дней Pro)"""
        now = datetime.utcnow()
        
        if user.subscription_expires_at and user.subscription_expires_at > now:
            user.subscription_expires_at += timedelta(days=30)
        else:
            user.subscription_expires_at = now + timedelta(days=30)
        
        user.subscription_tier = SubscriptionTier.PRO
        
        await self.db.commit()
        await self.db.refresh(user)
        
        print(f"🎁 User {user.telegram_id} got 30 days Pro for referrals")
        
        return user
    
    def get_pricing_info(self) -> dict:
        """Информация о ценах для отображения"""
        return {
            "plans": [
                {
                    "id": "sos_24h",
                    "name": "SOS",
                    "description": "Когда экзамен завтра 🔥",
                    "price_stars": PRICES["sos_24h"],
                    "price_uzs": "~12,000 UZS",
                    "price_usd": "$0.99",
                    "duration": "24 часа",
                    "features": ["Безлимит на 24ч", "Все Pro функции"],
                    "popular": False,
                },
                {
                    "id": "pro_monthly",
                    "name": "Pro",
                    "description": "Для отличников",
                    "price_stars": PRICES["pro_monthly"],
                    "price_uzs": "~65,000 UZS",
                    "price_usd": "$4.99",
                    "duration": "1 месяц",
                    "features": [
                        "Безлимитные генерации",
                        "🎧 Audio-Dialog",
                        "💬 AI-Debate",
                        "📊 Презентации",
                        "🔍 Vector Search",
                    ],
                    "popular": True,
                },
                {
                    "id": "pro_yearly",
                    "name": "Pro Год",
                    "description": "Максимальная выгода",
                    "price_stars": PRICES["pro_yearly"],
                    "price_uzs": "~520,000 UZS",
                    "price_usd": "$39.99",
                    "duration": "1 год",
                    "discount": "33%",
                    "features": [
                        "Всё из Pro",
                        "Скидка 33%",
                        "Приоритетная поддержка",
                    ],
                    "popular": False,
                },
            ],
            "free_tier": {
                "name": "Starter",
                "price": "Бесплатно",
                "daily_limit": 5,
                "features": [
                    "5 генераций в день",
                    "Smart Notes",
                    "Тесты и карточки",
                    "Группы",
                ],
            },
        }