# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduAI Assistant"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduai"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBAPP_URL: Optional[str] = None
    
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Бесплатный, быстрый
    MAX_CONTENT_LENGTH: int = 30000  # ~30k символов для Gemini

    # OpenAI
    OPENAI_API_KEY: str = " "
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    
    # Rate limits (Free tier)
    FREE_DAILY_LIMIT: int = 3
    
    class Config:
        env_file = ".env"

settings = Settings()