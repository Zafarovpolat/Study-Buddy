# backend/app/models/ai_output.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class OutputFormat:
    """Константы форматов вывода"""
    SMART_NOTES = "smart_notes"
    TLDR = "tldr"
    QUIZ = "quiz"
    GLOSSARY = "glossary"
    FLASHCARDS = "flashcards"
    PODCAST_SCRIPT = "podcast_script"


class AIOutput(Base):
    __tablename__ = "ai_outputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    
    # VARCHAR вместо ENUM!
    format = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    material = relationship("Material", back_populates="outputs")