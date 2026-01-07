"""Celery tasks for video generation."""
import time
from typing import Dict, Any
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app.celery_config import celery_app
from app.utils.logger import get_logger
from app.monitoring.metrics import (
    record_job_completion,
    record_job_processing_time,
    update_queue_depth,
    update_provider_health
)

logger = get_logger(__name__)


class CallbackTask(Task):
    """Base task with callbacks."""
    
    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task failure.
        
        Args:
            exc: Exception that caused failure
            task_id: Task ID
            args: Task args
            kwargs: Task kwargs
            einfo: Exception info
        """
        logger.error(
            "Task failed",
            task_id=task_id,
            error=str(exc),
            args=args,
            kwargs=kwargs
        )
        
        if args:
            job_id = args[0]
            self._update_job_status(job_id, "failed", str(exc))
    
    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        """Handle task retry.
        
        Args:
            exc: Exception that caused retry
            task_id: Task ID
            args: Task args
            kwargs: Task kwargs
            einfo: Exception info
        """
        logger.warning(
            "Task retry",
            task_id=task_id,
            error=str(exc),
            args=args,
            kwargs=kwargs
        )
    
    def _update_job_status(self, job_id: str, status: str, error_message: str = None) -> None:
        """Update job status in database.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if failed
        """
        try:
            import asyncio
            from app.db.prisma import get_prisma
            from app.db.models import update_job_status
            
            async def update():
                db = await get_prisma()
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status=status,
                    error_message=error_message
                )
            
            asyncio.run(update())
        except Exception as e:
            logger.error("Failed to update job status", job_id=job_id, error=str(e))


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.celery_app.tasks.process_video_generation",
    max_retries=3,
    default_retry_delay=60
)
def process_video_generation(self: Task, job_id: str) -> Dict[str, Any]:
    """Process video generation job.
    
    Args:
        self: Task instance
        job_id: Job ID to process
        
    Returns:
        Job result
        
    Raises:
        Exception: If processing fails
    """
    logger.info("Starting video generation", job_id=job_id, task_id=self.request.id)
    
    start_time = time.time()
    
    try:
        import asyncio
        from app.db.prisma import get_prisma
        from app.db.models import get_job, update_job_status
        
        async def process():
            db = await get_prisma()
            
            job = await get_job(db=db, job_id=job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            await update_job_status(
                db=db,
                job_id=job_id,
                status="processing"
            )
            
            logger.info("Processing job", job_id=job_id, prompt=job.prompt[:100])
            
            # Enhanced provider selection logic for phase 1.2
            from app.db.models import get_provider_health
            providers = await get_provider_health(db=db)
            healthy_providers = [p for p in providers if p.status == "healthy"]
            
            if healthy_providers:
                # Phase 1.2: Implement intelligent provider selection
                selected_provider = await _select_best_provider(healthy_providers, job.prompt)
                provider_name = selected_provider.provider
                
                # Select appropriate model based on job requirements
                model_name = await _select_best_model(selected_provider, job.prompt)
            else:
                # Enhanced fallback logic
                provider_name, model_name = await _get_fallback_provider(db)
            
            time.sleep(2)
            
            result = {
                "video_url": f"https://example.com/videos/{job_id}.mp4",
                "thumbnail_url": f"https://example.com/thumbnails/{job_id}.jpg",
                "duration_seconds": 10,
                "resolution": "1920x1080"
            }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Update provider metrics based on job completion
            await _update_provider_metrics(db, provider_name, duration_ms, True)
            
            await update_job_status(
                db=db,
                job_id=job_id,
                status="completed",
                result=result,
                used_provider=provider_name,
                used_model=model_name,
                generation_time_ms=duration_ms
            )
            
            record_job_completion("completed")
            record_job_processing_time(
                duration_seconds=(time.time() - start_time),
                provider=provider_name,
                model=model_name
            )
            
            logger.info("Job completed", job_id=job_id, duration_ms=duration_ms, provider=provider_name)
            
            return result
        
        result = asyncio.run(process())
        return result
        
    except SoftTimeLimitExceeded:
        logger.error("Task time limit exceeded", job_id=job_id)
        self._update_job_status(job_id, "failed", "Task time limit exceeded")
        record_job_completion("failed")
        raise
        
    except Exception as e:
        logger.error("Job processing failed", job_id=job_id, error=str(e))

        # Update provider metrics on failure
        if 'provider_name' in locals():
            async def update_failure_metrics():
                db = await get_prisma()
                await _update_provider_metrics(db, provider_name, 0, False)
            asyncio.run(update_failure_metrics())

        if self.request.retries < self.max_retries:
            retry_delay = self.default_retry_delay * (2 ** self.request.retries)
            logger.info("Retrying job", job_id=job_id, retry_count=self.request.retries + 1)
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            self._update_job_status(job_id, "failed", str(e))
            record_job_completion("failed")
            raise


async def _select_best_provider(providers, prompt: str):
    """Select the best provider based on multiple criteria.
    
    Args:
        providers: List of healthy providers
        prompt: Job prompt for capability matching
        
    Returns:
        Selected provider
    """
    if not providers:
        return None
    
    # Phase 1.2: Multi-criteria provider selection
    # 1. Filter by capabilities first
    capable_providers = []
    for provider in providers:
        if provider.metadata and "capabilities" in provider.metadata:
            # Simple capability matching - look for keywords in prompt
            prompt_lower = prompt.lower()
            has_capability = any(
                cap in prompt_lower 
                for cap in provider.metadata["capabilities"]
            )
            if has_capability:
                capable_providers.append(provider)
    
    # If no providers match capabilities, use all healthy providers
    if not capable_providers:
        capable_providers = providers
    
    # 2. Sort by cost (ascending) and response time (ascending)
    sorted_providers = sorted(
        capable_providers,
        key=lambda p: (
            p.costPerRequest or float('inf'),  # Lower cost first
            p.avgResponseTimeMs or 0           # Lower response time first
        )
    )
    
    # 3. Add load balancing - rotate through top providers
    # This prevents overloading a single provider
    if len(sorted_providers) > 1:
        # Simple round-robin: pick based on hash of current time
        import time
        current_time = int(time.time())
        index = current_time % min(3, len(sorted_providers))
        return sorted_providers[index]
    
    return sorted_providers[0]


async def _select_best_model(provider, prompt: str):
    """Select the best model for a provider based on job requirements.
    
    Args:
        provider: Selected provider
        prompt: Job prompt
        
    Returns:
        Selected model name
    """
    if not provider.metadata or "models" not in provider.metadata:
        return "default-model"
    
    models = provider.metadata["models"]
    if not models:
        return "default-model"
    
    # Phase 1.2: Simple model selection based on prompt complexity
    prompt_length = len(prompt)
    
    # For longer prompts, prefer more advanced models (last in list)
    if prompt_length > 500 and len(models) > 1:
        return models[-1]  # Most advanced model
    
    # For shorter prompts, use first model (usually fastest/cheapest)
    return models[0]


async def _get_fallback_provider(db):
    """Get fallback provider when no healthy providers are available.
    
    Args:
        db: Database client
        
    Returns:
        Tuple of (provider_name, model_name)
    """
    # Try to find any provider (even unhealthy ones) as last resort
    from app.db.models import get_provider_health
    all_providers = await get_provider_health(db=db)
    
    if all_providers:
        # Pick the one with fewest consecutive failures
        sorted_providers = sorted(
            all_providers,
            key=lambda p: p.consecutiveFailures or float('inf')
        )
        provider = sorted_providers[0]
        
        if provider.metadata and "models" in provider.metadata and provider.metadata["models"]:
            return provider.provider, provider.metadata["models"][0]
        else:
            return provider.provider, "fallback-model"
    
    # Absolute fallback
    return "mock_provider", "mock_model"


async def _update_provider_metrics(db, provider_name: str, duration_ms: int, success: bool):
    """Update provider performance metrics after job completion.
    
    Args:
        db: Database client
        provider_name: Provider name
        duration_ms: Job duration in milliseconds
        success: Whether job succeeded
    """
    try:
        from app.db.models import get_provider_health, update_provider_health
        
        # Get current provider health
        provider_health = await get_provider_health(db=db, provider=provider_name)
        current_health = provider_health[0] if provider_health else None
        
        # Update metrics
        avg_response_time = duration_ms
        consecutive_failures = 0
        
        if not success:
            consecutive_failures = (current_health.consecutiveFailures + 1) if current_health else 1
        
        # Update health status based on recent performance
        if success:
            status = "healthy"
        else:
            status = "unhealthy" if consecutive_failures >= 3 else "degraded"
        
        await update_provider_health(
            db=db,
            provider=provider_name,
            status=status,
            error_message=None if success else "Job processing failed",
            response_time_ms=avg_response_time,
            consecutive_failures=consecutive_failures
        )
        
        # Update Prometheus metrics
        update_provider_health(provider_name, status)
        
    except Exception as e:
        logger.error("Failed to update provider metrics", provider=provider_name, error=str(e))


@celery_app.task(name="app.celery_app.tasks.update_queue_metrics")
def update_queue_metrics() -> None:
    """Update queue depth metrics."""
    try:
        from app.config import settings
        import redis
        
        client = redis.from_url(settings.REDIS_URL)
        
        for queue_name in [
            settings.DEFAULT_QUEUE_NAME,
            settings.HIGH_PRIORITY_QUEUE_NAME,
            settings.LOW_PRIORITY_QUEUE_NAME
        ]:
            depth = client.llen(queue_name)
            update_queue_depth(queue_name, depth)
        
        client.close()
    except Exception as e:
        logger.error("Failed to update queue metrics", error=str(e))
