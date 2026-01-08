"""Celery tasks for video generation.

The platform processes video generation asynchronously. The primary task is
`generate_video`, which orchestrates provider selection, generation, storage, and
status tracking.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app.celery_config import celery_app
from app.monitoring.metrics import (
    record_job_completion,
    record_job_processing_time,
    update_queue_depth,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CallbackTask(Task):
    """Base task with callbacks."""

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Handle task failure."""

        logger.error(
            "Task failed",
            task_id=task_id,
            error=str(exc),
            args=args,
            kwargs=kwargs,
        )

        if args:
            job_id = args[0]
            self._update_job_status(job_id, "failed", str(exc))

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Handle task retry."""

        logger.warning(
            "Task retry",
            task_id=task_id,
            error=str(exc),
            args=args,
            kwargs=kwargs,
        )

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Update job status in database (best-effort)."""

        try:
            import asyncio

            from app.db.models import update_job_status
            from app.db.prisma import get_prisma

            async def update() -> None:
                db = await get_prisma()
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status=status,
                    error_message=error_message,
                )

            asyncio.run(update())
        except Exception as e:  # pragma: no cover
            logger.error("Failed to update job status", job_id=job_id, error=str(e))


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.celery_app.tasks.generate_video",
    max_retries=3,
    default_retry_delay=60,
)
def generate_video(self: Task, job_id: str) -> Dict[str, Any]:
    """Generate a video for the given job."""

    logger.info("Starting video generation", job_id=job_id, task_id=self.request.id)
    start_time = time.time()

    try:
        import asyncio

        from app.db.models import (
            get_job,
            update_job_metadata,
            update_job_status,
            update_provider_health,
        )
        from app.db.prisma import get_prisma
        from app.video.pipeline import generate_video_for_job

        async def process() -> Dict[str, Any]:
            db = await get_prisma()
            job = await get_job(db=db, job_id=job_id)
            if job is None:
                raise ValueError(f"Job {job_id} not found")

            if job.status == "cancelled":
                return {"status": "cancelled"}

            await update_job_status(db=db, job_id=job_id, status="processing")
            await update_job_metadata(
                db=db,
                job_id=job_id,
                metadata_patch={"progress": 5, "statusMessage": "Starting"},
            )

            try:
                pipeline_result = await generate_video_for_job(
                    job_id=job.id,
                    user_id=job.userId,
                    prompt=job.prompt,
                    metadata=job.metadata,
                )
            except Exception as e:
                await update_job_metadata(
                    db=db,
                    job_id=job_id,
                    metadata_patch={"progress": 100, "statusMessage": "Failed"},
                )
                raise e

            await update_job_metadata(
                db=db,
                job_id=job_id,
                metadata_patch={"progress": 100, "statusMessage": "Completed"},
            )

            duration_ms = pipeline_result["generation_time_ms"]
            used_provider = pipeline_result["used_provider"]
            used_model = pipeline_result.get("used_model")
            result = pipeline_result["result"]

            await update_job_status(
                db=db,
                job_id=job_id,
                status="completed",
                result=result,
                used_provider=used_provider,
                used_model=used_model,
                generation_time_ms=duration_ms,
            )

            await update_provider_health(
                db=db,
                provider=used_provider,
                status="healthy",
                response_time_ms=duration_ms,
            )

            record_job_completion("completed")
            record_job_processing_time(
                duration_seconds=(time.time() - start_time),
                provider=used_provider,
                model=used_model or "unknown",
            )

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

        self._update_job_status(job_id, "failed", str(e))
        record_job_completion("failed")
        raise


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.celery_app.tasks.process_video_generation",
)
def process_video_generation(self: Task, job_id: str) -> Dict[str, Any]:
    """Backward-compatible alias for `generate_video`."""

    return generate_video(self, job_id)


@celery_app.task(name="app.celery_app.tasks.poll_provider_status")
def poll_provider_status(job_id: str, provider_job_id: str) -> Dict[str, Any]:
    """Poll provider status for async providers.

    This is currently a placeholder for providers that expose asynchronous job
    handles.
    """

    return {"job_id": job_id, "provider_job_id": provider_job_id, "status": "unknown"}


@celery_app.task(name="app.celery_app.tasks.download_video")
def download_video(job_id: str, video_url: str) -> Dict[str, Any]:
    """Download a video from a provider URL.

    The main pipeline performs downloading inline today; this task exists to
    support future async provider flows.
    """

    return {"job_id": job_id, "video_url": video_url}


@celery_app.task(name="app.celery_app.tasks.cleanup_expired_videos")
def cleanup_expired_videos() -> Dict[str, Any]:
    """Clean up expired videos on local storage.

    For local storage, expiration is based on file modification time.
    """

    from datetime import datetime, timedelta
    from pathlib import Path

    from app.config import settings

    base = Path(settings.VIDEO_STORAGE_PATH).expanduser().resolve()
    if not base.exists():
        return {"deleted": 0}

    cutoff = datetime.utcnow() - timedelta(days=settings.VIDEO_RETENTION_DAYS)
    deleted = 0

    for path in base.rglob("*"):
        if not path.is_file():
            continue
        try:
            mtime = datetime.utcfromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                path.unlink(missing_ok=True)
                deleted += 1
        except Exception:  # pragma: no cover
            continue

    return {"deleted": deleted}


@celery_app.task(name="app.celery_app.tasks.update_queue_metrics")
def update_queue_metrics() -> None:
    """Update queue depth metrics."""

    try:
        import redis

        from app.config import settings

        client = redis.from_url(settings.REDIS_URL)

        for queue_name in [
            settings.DEFAULT_QUEUE_NAME,
            settings.HIGH_PRIORITY_QUEUE_NAME,
            settings.LOW_PRIORITY_QUEUE_NAME,
        ]:
            depth = client.llen(queue_name)
            update_queue_depth(queue_name, depth)

        client.close()
    except Exception as e:  # pragma: no cover
        logger.error("Failed to update queue metrics", error=str(e))
