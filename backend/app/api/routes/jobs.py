"""Job API routes."""
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from app.api.models.job import JobCreate, JobResponse, JobListResponse, JobStatsResponse
from app.db.prisma import get_prisma
from app.db.models import (
    create_job,
    get_job,
    list_jobs,
    delete_job,
    update_job_status,
    get_job_stats,
)
from app.celery_app.celery_config import celery_app
from app.celery_app.tasks import process_video_generation
from app.utils.errors import JobNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job_endpoint(job_data: JobCreate) -> JobResponse:
    """Create a new video generation job.

    Args:
        job_data: Job creation data

    Returns:
        Created job
    """
    db = await get_prisma()

    job = await create_job(
        db=db,
        user_id=job_data.userId,
        prompt=job_data.prompt,
        metadata=job_data.metadata,
        max_retries=job_data.maxRetries,
    )

    task = process_video_generation.delay(job.id)

    # Update job with Celery task ID
    job = await update_job_status(
        db=db, job_id=job.id, status="queued", celery_task_id=task.id
    )

    logger.info(
        "Job created and queued",
        job_id=job.id,
        user_id=job_data.userId,
        task_id=task.id,
    )

    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(job_id: str) -> JobResponse:
    """Get job by ID.

    Args:
        job_id: Job ID

    Returns:
        Job details

    Raises:
        JobNotFoundError: If job not found
    """
    db = await get_prisma()

    job = await get_job(db=db, job_id=job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    return JobResponse.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs_endpoint(
    userId: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    take: int = Query(50, ge=1, le=100, description="Number of records to return"),
) -> JobListResponse:
    """List jobs with filters and pagination.

    Args:
        userId: Filter by user ID
        status: Filter by status
        skip: Number of records to skip
        take: Number of records to return

    Returns:
        Paginated job list
    """
    db = await get_prisma()

    jobs = await list_jobs(db=db, user_id=userId, status=status, skip=skip, take=take)

    total = await db.job.count(
        where={
            **({"userId": userId} if userId else {}),
            **({"status": status} if status else {}),
        }
    )

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        take=take,
    )


@router.delete("/{job_id}", status_code=204)
async def delete_job_endpoint(job_id: str) -> None:
    """Delete/cancel a job.

    Args:
        job_id: Job ID

    Raises:
        JobNotFoundError: If job not found
    """
    db = await get_prisma()

    job = await get_job(db=db, job_id=job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    # Revoke Celery task if ID exists
    if job.celeryTaskId:
        celery_app.control.revoke(job.celeryTaskId, terminate=True)
        logger.info(
            "Revoked Celery task before deletion",
            job_id=job_id,
            task_id=job.celeryTaskId,
        )

    await delete_job(db=db, job_id=job_id)

    logger.info("Job deleted", job_id=job_id)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job_endpoint(job_id: str) -> JobResponse:
    """Cancel a running or queued job.

    Args:
        job_id: Job ID

    Returns:
        Updated job details

    Raises:
        JobNotFoundError: If job not found
        HTTPException: If job cannot be cancelled
    """
    db = await get_prisma()

    job = await get_job(db=db, job_id=job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, detail=f"Job in status {job.status} cannot be cancelled"
        )

    # Revoke Celery task if ID exists
    if job.celeryTaskId:
        celery_app.control.revoke(job.celeryTaskId, terminate=True)
        logger.info("Revoked Celery task", job_id=job_id, task_id=job.celeryTaskId)

    # Update job status
    job = await update_job_status(
        db=db, job_id=job_id, status="cancelled", error_message="Job cancelled by user"
    )

    return JobResponse.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job_endpoint(job_id: str) -> JobResponse:
    """Retry a failed or cancelled job.

    Args:
        job_id: Job ID

    Returns:
        Updated job details

    Raises:
        JobNotFoundError: If job not found
        HTTPException: If job cannot be retried
    """
    db = await get_prisma()

    job = await get_job(db=db, job_id=job_id)

    if not job:
        raise JobNotFoundError(job_id=job_id)

    if job.status not in ["failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only failed or cancelled jobs can be retried. Current status: {job.status}",
        )

    # Reset job status and retry count
    job = await update_job_status(
        db=db, job_id=job_id, status="queued", error_message=None
    )

    # Queue new task
    task = process_video_generation.delay(job.id)

    # Update job with new task ID
    job = await update_job_status(
        db=db, job_id=job.id, status="queued", celery_task_id=task.id
    )

    logger.info("Job retried", job_id=job_id, task_id=task.id)

    return JobResponse.model_validate(job)


@router.get("/stats/summary", response_model=JobStatsResponse)
async def get_jobs_stats_endpoint(
    userId: Optional[str] = Query(None, description="Filter by user ID")
) -> JobStatsResponse:
    """Get job statistics summary.

    Args:
        userId: Filter by user ID

    Returns:
        Job statistics summary
    """
    db = await get_prisma()

    stats = await get_job_stats(db=db, user_id=userId)

    return JobStatsResponse(**stats)
