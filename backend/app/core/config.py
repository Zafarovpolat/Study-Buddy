# backend/app/core/config.py - ЗАМЕНИ ПОЛНОСТЬЮ
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduAI Assistant"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduai"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    # AI - Gemini 2.0 Flash
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Новая модель!
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    
    # Rate limits
    FREE_DAILY_LIMIT: int = 3
    MAX_CONTENT_LENGTH: int = 50000  # Gemini 2.0 поддерживает больше
    
    # Frontend URL
    FRONTEND_URL: str = ""
    
    class Config:
        env_file = ".env"
        extra = "allow"
    
    def get_database_url(self) -> str:
        """Преобразует DATABASE_URL в формат для asyncpg"""
        url = self.DATABASE_URL
        
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url


settings = Settings()