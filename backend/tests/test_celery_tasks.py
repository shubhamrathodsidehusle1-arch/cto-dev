"""Tests for Celery tasks."""
import pytest
from unittest.mock import MagicMock, patch
from app.celery_app.tasks import process_video_generation, update_queue_metrics


@pytest.mark.asyncio
async def test_process_video_generation_success(db):
    """Test successful video generation task.
    
    Args:
        db: Prisma client
    """
    from app.db.models import create_job
    
    job = await create_job(
        db=db,
        user_id="test-user",
        prompt="Test prompt"
    )
    
    # Mock provider health
    from app.db.models import update_provider_health
    await update_provider_health(
        db=db,
        provider="test_provider",
        status="healthy",
        response_time_ms=100,
        metadata={"models": ["model1", "model2"]}
    )
    
    # Execute task (synchronously for testing)
    result = process_video_generation(job_id=job.id)
    
    # Verify job was updated
    from app.db.models import get_job
    updated_job = await get_job(db=db, job_id=job.id)
    
    assert updated_job.status == "completed"
    assert updated_job.result is not None
    assert "video_url" in updated_job.result
    assert updated_job.usedProvider == "test_provider"


@pytest.mark.asyncio
async def test_process_video_generation_job_not_found(db):
    """Test video generation task with non-existent job.
    
    Args:
        db: Prisma client
    """
    with pytest.raises(ValueError, match="Job .* not found"):
        process_video_generation(job_id="non-existent-id")


@pytest.mark.asyncio
async def test_process_video_generation_with_no_providers(db):
    """Test video generation task with no healthy providers.
    
    Args:
        db: Prisma client
    """
    from app.db.models import create_job
    
    job = await create_job(
        db=db,
        user_id="test-user",
        prompt="Test prompt"
    )
    
    # No healthy providers available
    result = process_video_generation(job_id=job.id)
    
    # Verify job still completes with mock provider
    from app.db.models import get_job
    updated_job = await get_job(db=db, job_id=job.id)
    
    assert updated_job.status == "completed"
    assert updated_job.usedProvider == "mock_provider"


@pytest.mark.asyncio
async def test_process_video_generation_with_error(db):
    """Test video generation task that encounters an error.
    
    Args:
        db: Prisma client
    """
    from app.db.models import create_job
    
    job = await create_job(
        db=db,
        user_id="test-user",
        prompt="Test prompt"
    )
    
    with patch('app.celery_app.tasks.time.sleep', side_effect=Exception("Simulated error")):
        with pytest.raises(Exception, match="Simulated error"):
            process_video_generation(job_id=job.id)
    
    # Verify job was marked as failed
    from app.db.models import get_job
    updated_job = await get_job(db=db, job_id=job.id)
    
    assert updated_job.status == "failed"
    assert "Simulated error" in updated_job.errorMessage


@pytest.mark.asyncio
async def test_update_queue_metrics_success(db):
    """Test updating queue metrics.
    
    Args:
        db: Prisma client
    """
    # This test just ensures the task runs without error
    # In a real scenario, you'd mock Redis to verify the calls
    with patch('app.celery_app.tasks.redis.from_url') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        mock_client.llen.return_value = 5
        
        update_queue_metrics()
        
        # Verify Redis was called for each queue
        assert mock_client.llen.call_count >= 3
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_process_video_generation_includes_model(db):
    """Test that video generation task picks a model from provider metadata.
    
    Args:
        db: Prisma client
    """
    from app.db.models import create_job, update_provider_health
    
    job = await create_job(
        db=db,
        user_id="test-user",
        prompt="Test prompt"
    )
    
    await update_provider_health(
        db=db,
        provider="test_provider",
        status="healthy",
        response_time_ms=100,
        metadata={"models": ["premium-model", "standard-model"]}
    )
    
    process_video_generation(job_id=job.id)
    
    from app.db.models import get_job
    updated_job = await get_job(db=db, job_id=job.id)
    
    assert updated_job.usedModel == "premium-model"


@pytest.mark.asyncio
async def test_process_video_generation_retry_logic(db):
    """Test that job retry count is managed correctly.
    
    Args:
        db: Prisma client
    """
    from app.db.models import create_job, update_provider_health
    
    job = await create_job(
        db=db,
        user_id="test-user",
        prompt="Test prompt",
        max_retries=3
    )
    
    await update_provider_health(
        db=db,
        provider="test_provider",
        status="healthy",
        response_time_ms=100
    )
    
    process_video_generation(job_id=job.id)
    
    from app.db.models import get_job
    updated_job = await get_job(db=db, job_id=job.id)
    
    # Retry count should be 0 on first success
    assert updated_job.retryCount == 0
