# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Lecto"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduai"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "lectoaibot"

    # AI - Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
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
        extra = "allow"
    
    def get_database_url(self) -> str:
        """Преобразует DATABASE_URL в формат для asyncpg"""
        url = self.DATABASE_URL
        
        # Заменяем протокол
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Для Supabase: используем порт 5432 (Session mode), НЕ 6543
        # Порт 6543 = Transaction mode (не работает с prepared statements)
        if "pooler.supabase.com:6543" in url:
            print("Warning: Using port 6543 (Transaction mode). Consider port 5432 (Session mode)")
        
        return url


settings = Settings()

# Отладка
print(f"GEMINI_MODEL: {settings.GEMINI_MODEL}")
print(f"GEMINI_API_KEY: {'***' + settings.GEMINI_API_KEY[-4:] if settings.GEMINI_API_KEY else 'NOT SET'}")
print(f"DATABASE: {'Supabase' if 'supabase' in settings.DATABASE_URL else 'Local'}")