"""Job API routes."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends, status
from prisma.models import User

from app.api.models.job import JobCreate, JobResponse, JobListResponse, JobStatsResponse
from app.api.dependencies import get_current_user
from app.db.prisma import get_prisma
from app.db.models import (
    create_job,
    get_job,
    list_jobs,
    delete_job,
    update_job_status,
    get_job_stats
)
from app.celery_app.celery_config import celery_app
from app.celery_app.tasks import process_video_generation
from app.utils.errors import JobNotFoundError, DatabaseError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job_endpoint(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Create a new video generation job.
    
    Args:
        job_data: Job creation data
        current_user: Current authenticated user
        
    Returns:
        Created job
    """
    db = await get_prisma()
    
    # Build metadata with video generation parameters
    metadata = job_data.metadata or {}
    if job_data.model:
        metadata["model"] = job_data.model
    if job_data.resolution:
        metadata["resolution"] = job_data.resolution
    if job_data.quality:
        metadata["quality"] = job_data.quality
    if job_data.duration:
        metadata["duration"] = job_data.duration
    
    job = await create_job(
        db=db,
        user_id=current_user.id,
        prompt=job_data.prompt,
        project_id=job_data.projectId,
        metadata=metadata,
        max_retries=job_data.maxRetries
    )
    
    task = process_video_generation.delay(job.id)
    
    # Update job with Celery task ID
    job = await update_job_status(
        db=db,
        job_id=job.id,
        status="queued",
        celery_task_id=task.id
    )
    
    logger.info("Job created and queued", job_id=job.id, user_id=job_data.userId, task_id=task.id)
    
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Get job by ID.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        
    Returns:
        Job details
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If user doesn't own the job
    """
    db = await get_prisma()
    
    job = await get_job(db=db, job_id=job_id)
    
    if not job:
        raise JobNotFoundError(job_id=job_id)
    
    # Verify user owns the job
    if job.userId != current_user.id:
        logger.warning(
            "Unauthorized job access attempt",
            job_id=job_id,
            user_id=current_user.id,
            owner_id=job.userId
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job"
        )
    
    return JobResponse.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs_endpoint(
    status: Optional[str] = Query(None, description="Filter by status"),
    projectId: Optional[str] = Query(None, description="Filter by project ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    take: int = Query(50, ge=1, le=100, description="Number of records to return"),
    current_user: User = Depends(get_current_user)
) -> JobListResponse:
    """List current user's jobs with filters and pagination.
    
    Args:
        status: Filter by status
        projectId: Filter by project ID
        skip: Number of records to skip
        take: Number of records to return
        current_user: Current authenticated user
        
    Returns:
        Paginated job list
    """
    db = await get_prisma()
    
    # Build where clause
    where: Dict[str, Any] = {"userId": current_user.id}
    if status:
        where["status"] = status
    if projectId:
        where["projectId"] = projectId
    
    jobs = await db.job.find_many(
        where=where,
        skip=skip,
        take=take,
        order={"createdAt": "desc"}
    )
    
    total = await db.job.count(where=where)
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        take=take
    )


@router.delete("/{job_id}", status_code=204)
async def delete_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete/cancel a job.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If user doesn't own the job
    """
    db = await get_prisma()
    
    job = await get_job(db=db, job_id=job_id)
    
    if not job:
        raise JobNotFoundError(job_id=job_id)
    
    # Verify user owns the job
    if job.userId != current_user.id:
        logger.warning(
            "Unauthorized job deletion attempt",
            job_id=job_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job"
        )
    
    # Revoke Celery task if ID exists
    if job.celeryTaskId:
        celery_app.control.revoke(job.celeryTaskId, terminate=True)
        logger.info("Revoked Celery task before deletion", job_id=job_id, task_id=job.celeryTaskId)
    
    await delete_job(db=db, job_id=job_id)
    
    logger.info("Job deleted", job_id=job_id, user_id=current_user.id)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Cancel a running or queued job.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        
    Returns:
        Updated job details
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If job cannot be cancelled or user doesn't own it
    """
    db = await get_prisma()
    
    job = await get_job(db=db, job_id=job_id)
    
    if not job:
        raise JobNotFoundError(job_id=job_id)
    
    # Verify user owns the job
    if job.userId != current_user.id:
        logger.warning(
            "Unauthorized job cancel attempt",
            job_id=job_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job"
        )
    
    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job in status {job.status} cannot be cancelled"
        )
    
    # Revoke Celery task if ID exists
    if job.celeryTaskId:
        celery_app.control.revoke(job.celeryTaskId, terminate=True)
        logger.info("Revoked Celery task", job_id=job_id, task_id=job.celeryTaskId)
    
    # Update job status
    job = await update_job_status(
        db=db,
        job_id=job_id,
        status="cancelled",
        error_message="Job cancelled by user"
    )
    
    logger.info("Job cancelled", job_id=job_id, user_id=current_user.id)
    
    return JobResponse.model_validate(job)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user)
) -> JobResponse:
    """Retry a failed or cancelled job.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        
    Returns:
        Updated job details
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If job cannot be retried or user doesn't own it
    """
    db = await get_prisma()
    
    job = await get_job(db=db, job_id=job_id)
    
    if not job:
        raise JobNotFoundError(job_id=job_id)
    
    # Verify user owns the job
    if job.userId != current_user.id:
        logger.warning(
            "Unauthorized job retry attempt",
            job_id=job_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this job"
        )
    
    if job.status not in ["failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only failed or cancelled jobs can be retried. Current status: {job.status}"
        )
    
    # Reset job status and retry count
    job = await update_job_status(
        db=db,
        job_id=job_id,
        status="queued",
        error_message=None
    )
    
    # Queue new task
    task = process_video_generation.delay(job.id)
    
    # Update job with new task ID
    job = await update_job_status(
        db=db,
        job_id=job.id,
        status="queued",
        celery_task_id=task.id
    )
    
    logger.info("Job retried", job_id=job_id, user_id=current_user.id, task_id=task.id)
    
    return JobResponse.model_validate(job)


@router.get("/stats/summary", response_model=JobStatsResponse)
async def get_jobs_stats_endpoint(
    current_user: User = Depends(get_current_user)
) -> JobStatsResponse:
    """Get current user's job statistics summary.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Job statistics summary
    """
    db = await get_prisma()
    
    stats = await get_job_stats(db=db, user_id=current_user.id)
    
    return JobStatsResponse(**stats)
