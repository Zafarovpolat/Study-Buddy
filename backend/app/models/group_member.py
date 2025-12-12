# backend/app/models/group_member.py
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class GroupRole:
    """Константы ролей"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # VARCHAR вместо ENUM!
    role = Column(String(20), default=GroupRole.MEMBER)
    joined_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    group = relationship("Folder", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
    
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_group_member'),
    )