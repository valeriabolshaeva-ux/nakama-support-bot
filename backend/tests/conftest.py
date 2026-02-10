"""
Pytest configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.models import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create in-memory SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_data(session: AsyncSession):
    """Create sample data for tests."""
    from app.database.models import Client, Project, UserBinding
    
    # Create client
    client = Client(name="Test Company")
    session.add(client)
    await session.flush()
    
    # Create projects
    project1 = Project(
        client_id=client.id,
        name="Main Project",
        invite_code="TEST001"
    )
    project2 = Project(
        client_id=client.id,
        name="Beta Project",
        invite_code="TEST002"
    )
    session.add_all([project1, project2])
    await session.flush()
    
    # Create user binding
    binding = UserBinding(
        tg_user_id=123456789,
        tg_username="testuser",
        tg_name="Test User",
        project_id=project1.id
    )
    session.add(binding)
    await session.commit()
    
    return {
        "client": client,
        "project1": project1,
        "project2": project2,
        "binding": binding,
    }
