"""Database initialization and session management."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from watchbot.config import AppConfig
from watchbot.core.models import Base

_engine = None
_session_factory = None


async def init_db(config: AppConfig) -> None:
    """Initialize the database engine and create tables."""
    global _engine, _session_factory

    _engine = create_async_engine(config.database.url, echo=config.debug)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory
