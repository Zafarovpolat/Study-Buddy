# backend/app/models/user.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
import secrets
from datetime import datetime

from app.models.base import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    SOS = "sos"  # 24-часовой доступ


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Подписка
    subscription_tier = Column(
        SQLEnum(SubscriptionTier), 
        default=SubscriptionTier.FREE,
        nullable=False
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Лимиты
    daily_requests = Column(Integer, default=0)
    last_request_date = Column(DateTime, nullable=True)
    
    # Streak
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    
    # Рефералы
    referral_code = Column(String(10), unique=True, nullable=True)
    referred_by_id = Column(UUID(as_uuid=True), nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def generate_referral_code(self) -> str:
        """Генерирует уникальный реферальный код"""
        if not self.referral_code:
            self.referral_code = secrets.token_hex(3).upper()
        return self.referral_code
    
    @property
    def is_pro(self) -> bool:
        """Проверяет активна ли Pro/SOS подписка"""
        if self.subscription_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at is None:
            return True  # Пожизненный Pro
        return self.subscription_expires_at > datetime.utcnow()
    
    @property
    def daily_limit(self) -> int:
        """Возвращает дневной лимит"""
        if self.is_pro:
            return 999999
        return 5
    
    def can_use_feature(self, feature: str) -> bool:
        """Проверяет доступ к Pro фиче"""
        pro_features = ['audio_dialog', 'ai_debate', 'presentation', 'vector_search']
        if feature in pro_features:
            return self.is_pro
        return True