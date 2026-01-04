"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient

from app.main import app
from app.db.prisma import get_prisma, disconnect_prisma


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session.

    Yields:
        Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.

    Yields:
        AsyncClient instance
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def db():
    """Create a database connection for testing.

    Yields:
        Prisma client
    """
    prisma = await get_prisma()
    yield prisma


@pytest.fixture(scope="function")
async def sample_job_data():
    """Sample job data for testing.

    Returns:
        Job creation data
    """
    return {
        "userId": "test-user-123",
        "prompt": "Create a video of a sunset over the ocean",
        "metadata": {"priority": "high", "tags": ["nature", "sunset"]},
        "maxRetries": 3,
    }
