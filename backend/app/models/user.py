# backend/app/models/user.py
from sqlalchemy import Column, String, Integer, DateTime, BigInteger, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import secrets
from datetime import datetime

from app.models.base import Base


class SubscriptionTier:
    FREE = "free"
    PRO = "pro"
    SOS = "sos"


# Лимиты по тарифам
TIER_LIMITS = {
    "free": {
        "daily_requests": 5,
        "max_groups": 3,
        "max_members_per_group": 5,
        "max_materials_per_group": 10,
        "audio_minutes": 15,
        "features": ["smart_notes_basic", "quiz", "flashcards", "glossary", "tldr"]
    },
    "pro": {
        "daily_requests": 999999,  # Безлимит
        "max_groups": 30,
        "max_members_per_group": 999999,  # Безлимит
        "max_materials_per_group": 999999,
        "audio_minutes": 120,
        "features": [
            "smart_notes_basic", "smart_notes_extended", 
            "quiz", "flashcards", "glossary", "tldr",
            "presentations", "debate", "audio_podcast", "vector_search"
        ]
    },
    "sos": {
        "daily_requests": 999999,
        "max_groups": 0,  # Нельзя создавать группы
        "max_members_per_group": 0,
        "max_materials_per_group": 999999,
        "audio_minutes": 120,
        "duration_hours": 24,
        "features": [
            "smart_notes_basic", "smart_notes_extended",
            "quiz", "flashcards", "glossary", "tldr",
            "presentations", "debate", "audio_podcast", "vector_search"
        ]
    }
}


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    subscription_tier = Column(
        String(20),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    
    daily_requests = Column(Integer, default=0)
    last_request_date = Column(DateTime, nullable=True)
    
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)
    
    referral_code = Column(String(10), unique=True, nullable=True)
    referred_by_id = Column(UUID(as_uuid=True), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_pro_granted = Column(Boolean, default=False)

    # Персонализация (Lecto 2.0)
    field_of_study = Column(String(50), nullable=True)  # law, economics, ir, it, medicine, other
    region = Column(String(20), default='global')        # uz, global
    preferred_language = Column(String(10), default='ru')
    onboarding_completed = Column(Boolean, default=False)
    
    # Геймификация
    intellect_points = Column(Integer, default=0)
    total_debates = Column(Integer, default=0)
    debates_won = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    perfect_quizzes = Column(Integer, default=0)  # 100% результат
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    materials = relationship("Material", back_populates="user")
    folders = relationship("Folder", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    group_memberships = relationship("GroupMember", back_populates="user")
    
    def generate_referral_code(self) -> str:
        if not self.referral_code:
            self.referral_code = secrets.token_hex(3).upper()
        return self.referral_code
    
    @property
    def effective_tier(self) -> str:
        """Возвращает актуальный тариф с учётом истечения подписки"""
        if self.subscription_tier == SubscriptionTier.FREE:
            return SubscriptionTier.FREE
        
        if self.subscription_expires_at is None:
            return self.subscription_tier
        
        if self.subscription_expires_at > datetime.utcnow():
            return self.subscription_tier
        
        return SubscriptionTier.FREE
    
    @property
    def is_pro(self) -> bool:
        """Pro или SOS с активной подпиской"""
        return self.effective_tier in [SubscriptionTier.PRO, SubscriptionTier.SOS]
    
    @property
    def tier_limits(self) -> dict:
        """Получить лимиты для текущего тарифа"""
        return TIER_LIMITS.get(self.effective_tier, TIER_LIMITS["free"])
    
    @property
    def daily_limit(self) -> int:
        return self.tier_limits["daily_requests"]
    
    @property
    def max_groups(self) -> int:
        return self.tier_limits["max_groups"]
    
    @property
    def max_members_per_group(self) -> int:
        return self.tier_limits["max_members_per_group"]
    
    @property
    def max_materials_per_group(self) -> int:
        return self.tier_limits["max_materials_per_group"]
    
    @property
    def audio_minutes_limit(self) -> int:
        return self.tier_limits["audio_minutes"]
    
    def can_use_feature(self, feature: str) -> bool:
        """Проверка доступа к функции"""
        return feature in self.tier_limits.get("features", [])