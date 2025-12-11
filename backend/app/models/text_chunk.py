# backend/app/models/text_chunk.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class TextChunk(Base):
    """Кусок текста с embedding для vector search"""
    __tablename__ = "text_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    
    # Текст куска
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Порядковый номер в материале
    
    # Embedding (вектор) — храним как массив float
    # Gemini text-embedding-004 даёт 768 dimensions
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Метаданные
    char_start = Column(Integer, nullable=True)  # Позиция начала в оригинальном тексте
    char_end = Column(Integer, nullable=True)
    
    # Relationships
    material = relationship("Material", back_populates="chunks")
    
    __table_args__ = (
        Index('ix_text_chunks_material_id', 'material_id'),
    )