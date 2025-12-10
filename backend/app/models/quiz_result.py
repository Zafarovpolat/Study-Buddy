# backend/app/models/quiz_result.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    
    score = Column(Integer, nullable=False)  # Правильных ответов
    max_score = Column(Integer, nullable=False)  # Всего вопросов
    percentage = Column(Integer, nullable=False)  # Процент
    
    completed_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    material = relationship("Material")