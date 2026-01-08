"""Tests for job API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_job(client: AsyncClient, sample_job_data, auth_context):
    """Test job creation endpoint."""

    headers, user_id = auth_context

    response = await client.post("/api/v1/jobs", json=sample_job_data, headers=headers)

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["userId"] == user_id
    assert data["prompt"] == sample_job_data["prompt"]
    assert data["status"] == "queued"
    assert data["retryCount"] == 0
    assert data["maxRetries"] == sample_job_data["maxRetries"]


@pytest.mark.asyncio
async def test_create_job_validation_error(client: AsyncClient, auth_context):
    """Test job creation with invalid data."""

    headers, _ = auth_context

    response = await client.post("/api/v1/jobs", json={"prompt": ""}, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job(client: AsyncClient, sample_job_data, auth_context):
    """Test getting job by ID."""

    headers, user_id = auth_context

    create_response = await client.post("/api/v1/jobs", json=sample_job_data, headers=headers)
    job_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == job_id
    assert data["userId"] == user_id


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient, auth_context):
    """Test getting non-existent job."""

    headers, _ = auth_context
    response = await client.get("/api/v1/jobs/non-existent-id", headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient, sample_job_data, auth_context):
    """Test listing jobs."""

    headers, _ = auth_context
    await client.post("/api/v1/jobs", json=sample_job_data, headers=headers)

    response = await client.get("/api/v1/jobs", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "jobs" in data
    assert "total" in data
    assert "skip" in data
    assert "take" in data
    assert isinstance(data["jobs"], list)


@pytest.mark.asyncio
async def test_list_jobs_with_filters(client: AsyncClient, sample_job_data, auth_context):
    """Test listing jobs with filters."""

    headers, user_id = auth_context

    await client.post("/api/v1/jobs", json=sample_job_data, headers=headers)

    response = await client.get("/api/v1/jobs", params={"status": "queued"}, headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert all(job["userId"] == user_id for job in data["jobs"])
    assert all(job["status"] == "queued" for job in data["jobs"])


@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient, sample_job_data, auth_context):
    """Test deleting a job."""

    headers, _ = auth_context

    create_response = await client.post("/api/v1/jobs", json=sample_job_data, headers=headers)
    job_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/jobs/{job_id}", headers=headers)

    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_not_found(client: AsyncClient, auth_context):
    """Test deleting non-existent job."""

    headers, _ = auth_context
    response = await client.delete("/api/v1/jobs/non-existent-id", headers=headers)

    assert response.status_code == 404
