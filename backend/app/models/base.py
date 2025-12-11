# backend/app/models/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

database_url = settings.get_database_url()
print(f"📦 Connecting to database...")

engine = create_async_engine(
    database_url, 
    echo=settings.DEBUG,
    pool_pre_ping=True,       # Проверяет соединение перед использованием
    pool_recycle=280,         # Переподключение каждые 4.5 минуты (до Supabase таймаута)
    pool_size=5,              # Базовый размер пула
    max_overflow=10,          # Дополнительные соединения при нагрузке
    pool_timeout=30,          # Таймаут ожидания соединения
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


__all__ = ["Base", "get_db", "engine", "AsyncSessionLocal"]