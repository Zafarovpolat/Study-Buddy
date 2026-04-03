# backend/app/models/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

database_url = settings.get_database_url()

print(f"📦 Connecting to database...")

# Настройки для asyncpg + Supabase PgBouncer
connect_args = {
    "statement_cache_size": 0,  # Обязательно для PgBouncer!
}

# Render обеспечивает SSL до Supabase — не нужно настраивать вручную
if "supabase" in database_url or "pooler.supabase" in database_url:
    print("🔒 SSL handled by Render proxy")

engine = create_async_engine(
    database_url,
    echo=False,
    poolclass=NullPool,  # Обязательно! Supabase сам делает pooling
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
    """Dependency для роутов"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


__all__ = ["Base", "get_db", "engine", "AsyncSessionLocal"]
