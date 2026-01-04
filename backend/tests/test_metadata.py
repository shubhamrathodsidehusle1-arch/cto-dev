"""Tests for metadata API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_metadata(client: AsyncClient):
    """Test getting all metadata.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/api/v1/metadata")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_get_metadata_by_key(client: AsyncClient):
    """Test getting metadata by key.
    
    Args:
        client: HTTP client
    """
    # First, set a metadata value
    await client.put("/api/v1/metadata/test_key", json={"value": "test_value"})
    
    # Then retrieve it
    response = await client.get("/api/v1/metadata/test_key")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["key"] == "test_key"
    assert data["value"] == "test_value"


@pytest.mark.asyncio
async def test_set_metadata(client: AsyncClient):
    """Test setting metadata.
    
    Args:
        client: HTTP client
    """
    response = await client.put(
        "/api/v1/metadata/new_key",
        json={"value": "new_value", "description": "Test metadata"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["key"] == "new_key"
    assert data["value"] == "new_value"


@pytest.mark.asyncio
async def test_delete_metadata(client: AsyncClient):
    """Test deleting metadata.
    
    Args:
        client: HTTP client
    """
    # First, set metadata
    await client.put("/api/v1/metadata/delete_test", json={"value": "test"})
    
    # Then delete it
    response = await client.delete("/api/v1/metadata/delete_test")
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get("/api/v1/metadata/delete_test")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_update_metadata(client: AsyncClient):
    """Test updating existing metadata.
    
    Args:
        client: HTTP client
    """
    # Set initial value
    await client.put("/api/v1/metadata/update_test", json={"value": "old_value"})
    
    # Update it
    response = await client.put(
        "/api/v1/metadata/update_test",
        json={"value": "new_value"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["value"] == "new_value"
