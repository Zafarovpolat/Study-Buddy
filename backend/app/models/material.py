from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base

class MaterialType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    AUDIO = "audio"
    LINK = "link"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    material_type = Column(Enum(MaterialType), nullable=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    raw_content = Column(Text, nullable=True)  # Извлечённый текст
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="materials")
    folder = relationship("Folder", back_populates="materials")
    outputs = relationship("AIOutput", back_populates="material", cascade="all, delete-orphan")