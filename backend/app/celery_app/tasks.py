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
    update_queue_depth
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
            
            time.sleep(2)
            
            result = {
                "video_url": f"https://example.com/videos/{job_id}.mp4",
                "thumbnail_url": f"https://example.com/thumbnails/{job_id}.jpg",
                "duration_seconds": 10,
                "resolution": "1920x1080"
            }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            await update_job_status(
                db=db,
                job_id=job_id,
                status="completed",
                result=result,
                used_provider="mock_provider",
                used_model="mock_model",
                generation_time_ms=duration_ms
            )
            
            record_job_completion("completed")
            record_job_processing_time(
                duration_seconds=(time.time() - start_time),
                provider="mock_provider",
                model="mock_model"
            )
            
            logger.info("Job completed", job_id=job_id, duration_ms=duration_ms)
            
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
        
        if self.request.retries < self.max_retries:
            retry_delay = self.default_retry_delay * (2 ** self.request.retries)
            logger.info("Retrying job", job_id=job_id, retry_count=self.request.retries + 1)
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            self._update_job_status(job_id, "failed", str(e))
            record_job_completion("failed")
            raise


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
