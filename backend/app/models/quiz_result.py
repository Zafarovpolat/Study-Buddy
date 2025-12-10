# backend/app/models/quiz_result.py - СОЗДАЙ НОВЫЙ ФАЙЛ
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentage = Column(Integer, nullable=False)
    
    completed_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="quiz_results")
    material = relationship("Material", backref="quiz_results")
    group = relationship("Folder", backref="quiz_results")