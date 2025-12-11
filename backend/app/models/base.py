# backend/app/models/base.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings

database_url = settings.get_database_url()

# Supabase требует SSL
if "supabase" in database_url and "sslmode" not in database_url:
    if "?" in database_url:
        database_url += "&sslmode=require"
    else:
        database_url += "?sslmode=require"

print(f"📦 Connecting to database...")

engine = create_async_engine(
    database_url, 
    echo=False,
    poolclass=NullPool,
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