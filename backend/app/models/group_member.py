# backend/app/models/group_member.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base


class GroupRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(Enum(GroupRole), default=GroupRole.MEMBER)
    joined_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    group = relationship("Folder", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
    
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='unique_group_member'),
    )