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
    pool_recycle=300,         # Переподключение каждые 5 минут
    pool_size=3,              # Меньше соединений для Free tier
    max_overflow=7,           # Итого макс 10 соединений
    pool_timeout=10,          # Быстрый таймаут
    pool_reset_on_return="rollback",  # Сброс транзакции при возврате в пул
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
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


__all__ = ["Base", "get_db", "engine", "AsyncSessionLocal"]