# backend/app/models/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

database_url = settings.get_database_url()

# Убираем sslmode из URL если есть
if "sslmode=" in database_url:
    database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")

print(f"📦 Connecting to database...")

# Настройки для Supabase Pooler
connect_args = {}
if "supabase" in database_url or "pooler.supabase" in database_url:
    connect_args = {
        "ssl": "require",
        "prepared_statement_cache_size": 0,  # Отключаем prepared statements
        "statement_cache_size": 0,           # Отключаем кеш
    }

engine = create_async_engine(
    database_url, 
    echo=False,
    poolclass=NullPool,
    connect_args=connect_args,
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


__all__ = ["Base", "get_db", "engine", "AsyncSessionLocal"]