# backend/app/models/user.py
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
import secrets
from datetime import datetime

from app.models.base import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    SOS = "sos"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    subscription_tier = Column(
        SQLEnum(SubscriptionTier), 
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
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    materials = relationship("Material", back_populates="user")
    folders = relationship("Folder", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    
    def generate_referral_code(self) -> str:
        if not self.referral_code:
            self.referral_code = secrets.token_hex(3).upper()
        return self.referral_code
    
    @property
    def is_pro(self) -> bool:
        if self.subscription_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at is None:
            return True
        return self.subscription_expires_at > datetime.utcnow()
    
    @property
    def daily_limit(self) -> int:
        if self.is_pro:
            return 999999
        return 5
    
    def can_use_feature(self, feature: str) -> bool:
        pro_features = ['audio_dialog', 'ai_debate', 'presentation', 'vector_search']
        if feature in pro_features:
            return self.is_pro
        return True