"""Tests for provider API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_provider_status(client: AsyncClient):
    """Test getting provider status.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/api/v1/providers/status")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_test_provider(client: AsyncClient):
    """Test provider testing endpoint.
    
    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/providers/test",
        json={"provider": "test_provider", "timeout": 30}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "provider" in data
    assert "status" in data
    assert data["provider"] == "test_provider"
