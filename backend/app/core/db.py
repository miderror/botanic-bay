# backend/app/core/db.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings
from app.utils.json_serializer import json_serializer

# Создаем асинхронный движок SQLAlchemy
engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=settings.POSTGRES_ECHO,
    json_serializer=json_serializer,
    future=True,
)

# Создаем фабрику асинхронных сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
