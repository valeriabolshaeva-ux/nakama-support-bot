"""
Pytest Configuration and Fixtures.

This module contains shared fixtures for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """
    Create a synchronous test client.
    
    Returns:
        TestClient: FastAPI test client for synchronous tests.
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:
    """
    Create an asynchronous test client.
    
    Returns:
        AsyncClient: HTTPX async client for async tests.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
