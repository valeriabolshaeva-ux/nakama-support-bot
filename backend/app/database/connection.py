"""
Database connection and session management.

Uses SQLAlchemy 2.0 async with aiosqlite for SQLite.
"""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

from typing import Optional

# Global engine instance
_engine: Optional[AsyncEngine] = None
_async_session: Optional[async_sessionmaker[AsyncSession]] = None


def get_database_url() -> str:
    """Get SQLite database URL."""
    return f"sqlite+aiosqlite:///{settings.db_path}"


def get_engine() -> AsyncEngine:
    """Get or create async engine."""
    global _engine
    
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=settings.log_level.lower() == "debug",
        )
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create async session factory."""
    global _async_session
    
    if _async_session is None:
        _async_session = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    return _async_session


async def init_db() -> None:
    """
    Initialize database: create tables if not exist.
    
    Should be called once at application startup.
    """
    # Ensure data directory exists
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info(f"Database initialized: {settings.db_path}")


async def close_db() -> None:
    """
    Close database connection.
    
    Should be called at application shutdown.
    """
    global _engine, _async_session
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session = None
        logger.info("Database connection closed")


async def get_session() -> AsyncSession:
    """
    Get a new database session.
    
    Usage:
        async with get_session() as session:
            # use session
            
    Or as dependency:
        session = await get_session()
        try:
            # use session
        finally:
            await session.close()
    """
    factory = get_session_factory()
    return factory()


class DatabaseSessionManager:
    """
    Context manager for database sessions.
    
    Usage:
        async with DatabaseSessionManager() as session:
            result = await session.execute(query)
    """
    
    def __init__(self) -> None:
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        factory = get_session_factory()
        self.session = factory()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
            await self.session.close()
