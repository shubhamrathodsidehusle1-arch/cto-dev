"""Tests for job API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_job(client: AsyncClient, sample_job_data):
    """Test job creation endpoint.

    Args:
        client: HTTP client
        sample_job_data: Sample job data
    """
    response = await client.post("/api/v1/jobs", json=sample_job_data)

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["userId"] == sample_job_data["userId"]
    assert data["prompt"] == sample_job_data["prompt"]
    assert data["status"] == "queued"
    assert data["retryCount"] == 0
    assert data["maxRetries"] == sample_job_data["maxRetries"]


@pytest.mark.asyncio
async def test_create_job_validation_error(client: AsyncClient):
    """Test job creation with invalid data.

    Args:
        client: HTTP client
    """
    response = await client.post(
        "/api/v1/jobs", json={"userId": "test-user", "prompt": ""}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job(client: AsyncClient, sample_job_data):
    """Test getting job by ID.

    Args:
        client: HTTP client
        sample_job_data: Sample job data
    """
    create_response = await client.post("/api/v1/jobs", json=sample_job_data)
    job_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == job_id
    assert data["userId"] == sample_job_data["userId"]


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient):
    """Test getting non-existent job.

    Args:
        client: HTTP client
    """
    response = await client.get("/api/v1/jobs/non-existent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient, sample_job_data):
    """Test listing jobs.

    Args:
        client: HTTP client
        sample_job_data: Sample job data
    """
    await client.post("/api/v1/jobs", json=sample_job_data)

    response = await client.get("/api/v1/jobs")

    assert response.status_code == 200
    data = response.json()

    assert "jobs" in data
    assert "total" in data
    assert "skip" in data
    assert "take" in data
    assert isinstance(data["jobs"], list)


@pytest.mark.asyncio
async def test_list_jobs_with_filters(client: AsyncClient, sample_job_data):
    """Test listing jobs with filters.

    Args:
        client: HTTP client
        sample_job_data: Sample job data
    """
    await client.post("/api/v1/jobs", json=sample_job_data)

    response = await client.get(
        "/api/v1/jobs", params={"userId": sample_job_data["userId"], "status": "queued"}
    )

    assert response.status_code == 200
    data = response.json()

    assert all(job["userId"] == sample_job_data["userId"] for job in data["jobs"])
    assert all(job["status"] == "queued" for job in data["jobs"])


@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient, sample_job_data):
    """Test deleting a job.

    Args:
        client: HTTP client
        sample_job_data: Sample job data
    """
    create_response = await client.post("/api/v1/jobs", json=sample_job_data)
    job_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/jobs/{job_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_not_found(client: AsyncClient):
    """Test deleting non-existent job.

    Args:
        client: HTTP client
    """
    response = await client.delete("/api/v1/jobs/non-existent-id")

    assert response.status_code == 404
