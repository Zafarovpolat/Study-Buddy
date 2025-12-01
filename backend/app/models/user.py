from sqlalchemy import Column, String, BigInteger, Enum, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    GROUP = "group"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    daily_requests_count = Column(BigInteger, default=0)
    last_request_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    materials = relationship("Material", back_populates="user")
    folders = relationship("Folder", back_populates="user")