"""Tests for database model operations."""
import pytest
from datetime import datetime
from prisma import Json

from app.db.models import (
    create_job,
    get_job,
    list_jobs,
    update_job,
    delete_job,
    update_provider_health,
    get_provider_health,
    create_metric,
)


@pytest.mark.asyncio
async def test_create_job_success(db):
    """Test successful job creation.
    
    Args:
        db: Prisma client
    """
    job = await create_job(
        db=db,
        user_id="test-user-1",
        prompt="A beautiful sunset over the ocean",
        metadata={"priority": "high", "tags": ["nature"]},
        max_retries=3
    )
    
    assert job.id is not None
    assert job.userId == "test-user-1"
    assert job.prompt == "A beautiful sunset over the ocean"
    assert job.status == "queued"
    assert job.retryCount == 0
    assert job.maxRetries == 3


@pytest.mark.asyncio
async def test_create_job_without_metadata(db):
    """Test job creation without metadata.
    
    Args:
        db: Prisma client
    """
    job = await create_job(
        db=db,
        user_id="test-user-2",
        prompt="Simple prompt without metadata"
    )
    
    assert job.id is not None
    assert job.userId == "test-user-2"
    assert job.metadata is None


@pytest.mark.asyncio
async def test_get_job_success(db):
    """Test getting a job by ID.
    
    Args:
        db: Prisma client
    """
    created = await create_job(
        db=db,
        user_id="test-user-3",
        prompt="Test prompt"
    )
    
    job = await get_job(db=db, job_id=created.id)
    
    assert job.id == created.id
    assert job.userId == "test-user-3"


@pytest.mark.asyncio
async def test_get_job_not_found(db):
    """Test getting non-existent job.
    
    Args:
        db: Prisma client
    """
    with pytest.raises(Exception):  # Should raise DatabaseError
        await get_job(db=db, job_id="non-existent-id")


@pytest.mark.asyncio
async def test_list_jobs_empty(db):
    """Test listing jobs when none exist.
    
    Args:
        db: Prisma client
    """
    jobs = await list_jobs(db=db)
    
    assert isinstance(jobs, list)


@pytest.mark.asyncio
async def test_list_jobs_with_results(db):
    """Test listing jobs with results.
    
    Args:
        db: Prisma client
    """
    await create_job(db=db, user_id="user-1", prompt="Prompt 1")
    await create_job(db=db, user_id="user-1", prompt="Prompt 2")
    await create_job(db=db, user_id="user-2", prompt="Prompt 3")
    
    jobs = await list_jobs(db=db)
    
    assert len(jobs) >= 3


@pytest.mark.asyncio
async def test_list_jobs_with_filters(db):
    """Test listing jobs with filters.
    
    Args:
        db: Prisma client
    """
    await create_job(db=db, user_id="user-1", prompt="Prompt 1")
    job2 = await create_job(db=db, user_id="user-2", prompt="Prompt 2")
    job3 = await create_job(db=db, user_id="user-2", prompt="Prompt 3")
    
    # Filter by user
    jobs = await list_jobs(db=db, user_id="user-2")
    assert all(j.userId == "user-2" for j in jobs)
    
    # Filter by status
    jobs = await list_jobs(db=db, status="queued")
    assert all(j.status == "queued" for j in jobs)
    
    # Filter with pagination
    jobs = await list_jobs(db=db, take=1)
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_update_job_status(db):
    """Test updating job status.
    
    Args:
        db: Prisma client
    """
    job = await create_job(db=db, user_id="user-1", prompt="Test")
    
    updated = await update_job(
        db=db,
        job_id=job.id,
        status="processing",
        retry_count=1
    )
    
    assert updated.id == job.id
    assert updated.status == "processing"
    assert updated.retryCount == 1


@pytest.mark.asyncio
async def test_update_job_with_result(db):
    """Test updating job with result.
    
    Args:
        db: Prisma client
    """
    job = await create_job(db=db, user_id="user-1", prompt="Test")
    
    result = {
        "videoUrl": "https://example.com/video.mp4",
        "thumbnailUrl": "https://example.com/thumb.jpg",
        "duration": 30
    }
    
    updated = await update_job(
        db=db,
        job_id=job.id,
        status="completed",
        result=result
    )
    
    assert updated.status == "completed"
    assert updated.result["videoUrl"] == result["videoUrl"]


@pytest.mark.asyncio
async def test_delete_job_success(db):
    """Test deleting a job.
    
    Args:
        db: Prisma client
    """
    job = await create_job(db=db, user_id="user-1", prompt="Test")
    
    deleted_job = await delete_job(db=db, job_id=job.id)
    
    assert deleted_job.id == job.id
    
    # Verify it's deleted
    with pytest.raises(Exception):
        await get_job(db=db, job_id=job.id)


@pytest.mark.asyncio
async def test_update_provider_health(db):
    """Test updating provider health.
    
    Args:
        db: Prisma client
    """
    health = await update_provider_health(
        db=db,
        provider="test-provider",
        status="healthy",
        error_message=None,
        response_time_ms=100,
        metadata={"endpoint": "https://api.test.com"}
    )
    
    assert health.provider == "test-provider"
    assert health.status == "healthy"
    assert health.avgResponseTimeMs == 100
    assert health.consecutiveFailures == 0


@pytest.mark.asyncio
async def test_update_provider_health_with_failure(db):
    """Test updating provider health with failure.
    
    Args:
        db: Prisma client
    """
    health = await update_provider_health(
        db=db,
        provider="test-provider",
        status="unhealthy",
        error_message="Connection timeout",
        response_time_ms=None
    )
    
    assert health.status == "unhealthy"
    assert health.lastErrorMessage == "Connection timeout"
    assert health.consecutiveFailures == 1


@pytest.mark.asyncio
async def test_get_provider_health(db):
    """Test getting provider health.
    
    Args:
        db: Prisma client
    """
    await update_provider_health(db=db, provider="provider-1", status="healthy")
    await update_provider_health(db=db, provider="provider-2", status="degraded")
    
    health_list = await get_provider_health(db=db)
    
    assert len(health_list) >= 2
    assert any(h.provider == "provider-1" for h in health_list)
    assert any(h.provider == "provider-2" for h in health_list)


@pytest.mark.asyncio
async def test_create_metric(db):
    """Test creating a metric.
    
    Args:
        db: Prisma client
    """
    metric = await create_metric(
        db=db,
        name="test_metric",
        value=42.5,
        labels={"env": "test", "service": "api"}
    )
    
    assert metric.id is not None
    assert metric.name == "test_metric"
    assert metric.value == 42.5
