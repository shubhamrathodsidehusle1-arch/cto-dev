"""Tests for error handling across the application."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_404_not_found(client: AsyncClient):
    """Test 404 error for non-existent endpoints.
    
    Args:
        client: HTTP client
    """
    response = await client.get("/api/v1/non-existent-endpoint")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_json_body(client: AsyncClient):
    """Test error handling for invalid JSON.
    
    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/jobs",
        content="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_missing_required_field(client: AsyncClient):
    """Test validation error for missing required fields.
    
    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/jobs",
        json={"userId": "test"}  # Missing required 'prompt' field
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_wrong_method(client: AsyncClient):
    """Test error for using wrong HTTP method.
    
    Args:
        client: HTTP client
    """
    # Try to use POST on a GET-only endpoint
    response = await client.post("/api/v1/providers/status")
    
    assert response.status_code in [405, 404]  # Method not allowed or not found


@pytest.mark.asyncio
async def test_invalid_content_type(client: AsyncClient):
    """Test error for invalid content type.
    
    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/jobs",
        data="test data",
        headers={"Content-Type": "text/plain"}
    )
    
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_empty_request_body(client: AsyncClient):
    """Test error handling for empty request body.
    
    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/jobs",
        json={}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_long_string_validation(client: AsyncClient):
    """Test validation for excessively long strings.
    
    Args:
        client: HTTP client
    """
    very_long_prompt = "x" * 100000  # 100k characters
    
    response = await client.post(
        "/api/v1/jobs",
        json={
            "userId": "test-user",
            "prompt": very_long_prompt
        }
    )
    
    # Should either accept or reject based on validation rules
    assert response.status_code in [201, 400, 422]


@pytest.mark.asyncio
async def test_special_characters_in_prompt(client: AsyncClient):
    """Test handling of special characters in prompt.
    
    Args:
        client: HTTP client
    """
    special_prompt = "Test with special chars: <script>alert('xss')</script> & \"quotes\" 'single' \n\t"
    
    response = await client.post(
        "/api/v1/jobs",
        json={
            "userId": "test-user",
            "prompt": special_prompt
        }
    )
    
    # Should handle special characters gracefully
    assert response.status_code in [201, 400, 422]
