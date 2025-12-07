# backend/app/models/ai_output.py - ЗАМЕНИ ПОЛНОСТЬЮ
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base


class OutputFormat(str, enum.Enum):
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
    
    format = Column(
        Enum(OutputFormat, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    material = relationship("Material", back_populates="outputs")