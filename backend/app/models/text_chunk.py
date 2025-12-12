# backend/app/models/text_chunk.py
from sqlalchemy import Column, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class TextChunk(Base):
    """Кусок текста с embedding для vector search"""
    __tablename__ = "text_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Embedding — массив float (768 dimensions для Gemini)
    embedding = Column(ARRAY(Float), nullable=True)
    
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    
    # Relationships
    material = relationship("Material", back_populates="chunks")