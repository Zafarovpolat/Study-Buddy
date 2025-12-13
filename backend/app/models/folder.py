# backend/app/models/folder.py
from sqlalchemy import Column, String, DateTime, ForeignKey, func, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import secrets

from app.models.base import Base


class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    
    # Group folder settings
    is_group = Column(Boolean, default=False, index=True)
    invite_code = Column(String(20), unique=True, nullable=True, index=True)
    description = Column(String(500), nullable=True)
    max_members = Column(Integer, default=50)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="folders", foreign_keys=[user_id])
    
    # Материалы в папке (через folder_id)
    materials = relationship(
        "Material", 
        foreign_keys="[Material.folder_id]",  # ✅ Строковая ссылка на FK
        back_populates="folder"
    )
    
    # Материалы в группе (через group_id)
    group_materials = relationship(
        "Material",
        foreign_keys="[Material.group_id]",  # ✅ Строковая ссылка на FK
        back_populates="group"
    )
    
    # Вложенные папки
    children = relationship(
        "Folder", 
        backref="parent", 
        remote_side=[id],
        foreign_keys=[parent_id]  # ✅ Явно указываем
    )
    
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="group")
    
    def generate_invite_code(self) -> str:
        if not self.invite_code:
            self.invite_code = secrets.token_urlsafe(8)[:10].upper()
        return self.invite_code
    
    @property
    def member_count(self) -> int:
        return len(self.members) if self.members else 0