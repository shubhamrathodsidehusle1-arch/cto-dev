"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator, Tuple
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def auth_context(client: AsyncClient) -> Tuple[dict, str]:
    """Create a user and return auth headers + user_id."""

    email = f"test-{uuid4()}@example.com"
    password = "Password123!"

    resp = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201

    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    user_id = me.json()["id"]

    return headers, user_id


@pytest.fixture(scope="function")
async def sample_job_data() -> dict:
    """Sample job data for testing."""

    return {
        "prompt": "Create a video of a sunset over the ocean",
        "metadata": {"priority": "high", "tags": ["nature", "sunset"]},
        "maxRetries": 3,
        "resolution": "1080p",
        "quality": "high",
        "duration": 10,
    }
