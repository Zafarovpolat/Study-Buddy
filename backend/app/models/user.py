# backend/app/models/user.py - ЗАМЕНИ ПОЛНОСТЬЮ
from sqlalchemy import Column, String, BigInteger, Integer, Enum, DateTime, Date, Boolean, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
import secrets

from app.models.base import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"      # ← значение должно быть lowercase!
    PRO = "pro"
    GROUP = "group"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    
    # Subscription
    subscription_tier = Column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x]),
        default=SubscriptionTier.FREE
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    telegram_payment_charge_id = Column(String(255), nullable=True)
    
    # Referral System
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referred_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    referral_pro_granted = Column(Boolean, default=False)
    
    # Rate limiting
    daily_requests_count = Column(BigInteger, default=0)
    last_request_date = Column(DateTime, nullable=True)
    
    # Streak tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    materials = relationship("Material", back_populates="user")
    folders = relationship("Folder", back_populates="user", foreign_keys="Folder.user_id")
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    group_memberships = relationship("GroupMember", back_populates="user")
    
    @property
    def is_pro(self) -> bool:
        if self.subscription_tier == SubscriptionTier.FREE:
            return False
        if self.subscription_expires_at:
            from datetime import datetime
            return self.subscription_expires_at > datetime.now()
        return True
    
    def generate_referral_code(self) -> str:
        if not self.referral_code:
            self.referral_code = secrets.token_urlsafe(8)[:10].upper()
        return self.referral_code