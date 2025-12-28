# backend/app/models/insight.py
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Источник
    source_url = Column(String(1000), nullable=True)
    source_name = Column(String(200), nullable=True)
    original_title = Column(String(500))
    original_content = Column(Text)
    
    # AI обработка
    title = Column(String(500))           # AI заголовок
    summary = Column(Text)                 # AI саммари
    importance = Column(Integer)           # 1-10
    importance_reason = Column(Text)       # Почему важно
    academic_link = Column(String(500))    # Связь с темой
    
    # Фильтрация
    field_of_study = Column(String(50))    # law, economics, ir...
    region = Column(String(20))            # uz, global
    
    # Метаданные
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Кэш сгенерированного конспекта
    detailed_content = Column(Text, nullable=True)