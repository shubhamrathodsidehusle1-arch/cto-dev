"""Tests for health check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Test liveness probe endpoint.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Test readiness probe endpoint.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test Prometheus metrics endpoint.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/metrics")
    
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
