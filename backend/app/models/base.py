# backend/app/models/base.py - ЗАМЕНИ ПОЛНОСТЬЮ
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# Получаем правильный URL для asyncpg
database_url = settings.get_database_url()
print(f"📦 Connecting to database...")  # Не выводим URL с паролем в логи

engine = create_async_engine(
    database_url, 
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    pool_recycle=300,    # Переподключение каждые 5 минут
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