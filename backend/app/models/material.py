# backend/app/models/material.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class MaterialType:
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"
    AUDIO = "audio"
    LINK = "link"
    TOPIC = "topic"


class ProcessingStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Material(Base):
    __tablename__ = "materials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    material_type = Column(String(20), nullable=False)
    status = Column(String(20), default=ProcessingStatus.PENDING)
    
    # ОБА ИМЕНИ для совместимости!
    extracted_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="materials")
    folder = relationship("Folder", back_populates="materials")
    outputs = relationship("AIOutput", back_populates="material", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="material", cascade="all, delete-orphan")
    chunks = relationship("TextChunk", back_populates="material", cascade="all, delete-orphan")
    
    # Property для совместимости — код использует raw_content
    @property
    def raw_content(self):
        return self.extracted_text
    
    @raw_content.setter
    def raw_content(self, value):
        self.extracted_text = value