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
    TELEGRAM_BOT_USERNAME: str = "studybuddy_uzbot"  # ДОБАВЬ ЭТО

    # AI - Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Читается из .env!
    
    # OpenAI (опционально)
    OPENAI_API_KEY: Optional[str] = None
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20
    
    # Rate limits
    FREE_DAILY_LIMIT: int = 100
    MAX_CONTENT_LENGTH: int = 50000
    
    # Frontend URL
    FRONTEND_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Разрешаем дополнительные переменные
    
    def get_database_url(self) -> str:
        """Преобразует DATABASE_URL в формат для asyncpg"""
        url = self.DATABASE_URL
        
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url


settings = Settings()

# Отладка - проверяем что настройки загружены
print(f"🔧 GEMINI_MODEL: {settings.GEMINI_MODEL}")
print(f"🔧 GEMINI_API_KEY: {'***' + settings.GEMINI_API_KEY[-4:] if settings.GEMINI_API_KEY else 'NOT SET'}")