# backend/app/core/config.py - ЗАМЕНИ ПОЛНОСТЬЮ
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduAI Assistant"
    DEBUG: bool = False
    
    # Database - Render даёт postgres://, но asyncpg требует postgresql+asyncpg://
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduai"
    
    # Redis (опционально)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    # AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    
    # Rate limits
    FREE_DAILY_LIMIT: int = 3
    MAX_CONTENT_LENGTH: int = 30000
    
    # Frontend URL
    FRONTEND_URL: str = ""
    
    class Config:
        env_file = ".env"
        extra = "allow"
    
    def get_database_url(self) -> str:
        """Преобразует DATABASE_URL в формат для asyncpg"""
        url = self.DATABASE_URL
        
        # Render даёт postgres://, но SQLAlchemy asyncpg требует postgresql+asyncpg://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Если URL уже правильный - возвращаем как есть
        if url.startswith("postgresql+asyncpg://"):
            return url
        
        # Если это просто hostname (ошибка конфигурации)
        if not "://" in url:
            raise ValueError(
                f"Invalid DATABASE_URL format: {url}. "
                "Expected full URL like: postgres://user:pass@host:5432/dbname"
            )
        
        return url


settings = Settings()