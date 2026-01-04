"""Database model helpers."""
from typing import Any, Dict, List, Optional
from datetime import datetime

from prisma.models import Job, ProviderHealth, Metric
from prisma import Json

from app.utils.errors import DatabaseError
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def get_system_metadata(db: Any, key: str) -> Optional[Any]:
    """Get system metadata by key.
    
    Args:
        db: Prisma client
        key: Metadata key
        
    Returns:
        Metadata value or None if not found
    """
    try:
        metadata = await db.systemmetadata.find_unique(where={"key": key})
        return metadata.value if metadata else None
    except Exception as e:
        logger.error("Failed to get system metadata", key=key, error=str(e))
        return None


async def create_job(
    db: Any,
    user_id: str,
    prompt: str,
    metadata: Optional[Dict[str, Any]] = None,
    max_retries: Optional[int] = None
) -> Job:
    """Create a new job.
    
    Args:
        db: Prisma client
        user_id: User ID
        prompt: Video generation prompt
        metadata: Additional metadata
        max_retries: Maximum retry attempts (overrides system default)
        
    Returns:
        Created job
        
    Raises:
        DatabaseError: If job creation fails
    """
    try:
        if max_retries is None:
            max_retries = await get_system_metadata(db, "default_max_retries") or 3
            
        job_data = {
            "userId": user_id,
            "prompt": prompt,
            "maxRetries": max_retries,
            "status": "queued"
        }
        
        if metadata is not None:
            job_data["metadata"] = Json(metadata)
            
        job = await db.job.create(data=job_data)
        logger.info("Job created", job_id=job.id, user_id=user_id)
        return job
    except Exception as e:
        logger.error("Failed to create job", error=str(e))
        raise DatabaseError(f"Failed to create job: {str(e)}")


async def get_job(db: Any, job_id: str) -> Optional[Job]:
    """Get job by ID.
    
    Args:
        db: Prisma client
        job_id: Job ID
        
    Returns:
        Job or None if not found
    """
    try:
        return await db.job.find_unique(where={"id": job_id})
    except Exception as e:
        logger.error("Failed to get job", job_id=job_id, error=str(e))
        raise DatabaseError(f"Failed to get job: {str(e)}")


async def list_jobs(
    db: Any,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    take: int = 50
) -> List[Job]:
    """List jobs with filters.
    
    Args:
        db: Prisma client
        user_id: Filter by user ID
        status: Filter by status
        skip: Number of records to skip
        take: Number of records to return
        
    Returns:
        List of jobs
    """
    try:
        where: Dict[str, Any] = {}
        if user_id:
            where["userId"] = user_id
        if status:
            where["status"] = status
        
        jobs = await db.job.find_many(
            where=where,
            skip=skip,
            take=take,
            order={"createdAt": "desc"}
        )
        return jobs
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise DatabaseError(f"Failed to list jobs: {str(e)}")


async def update_job_status(
    db: Any,
    job_id: str,
    status: str,
    error_message: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    used_provider: Optional[str] = None,
    used_model: Optional[str] = None,
    generation_time_ms: Optional[int] = None,
    celery_task_id: Optional[str] = None
) -> Job:
    """Update job status.
    
    Args:
        db: Prisma client
        job_id: Job ID
        status: New status
        error_message: Error message if failed
        result: Job result if completed
        used_provider: Provider used
        used_model: Model used
        generation_time_ms: Generation time in milliseconds
        celery_task_id: Celery task ID
        
    Returns:
        Updated job
        
    Raises:
        DatabaseError: If update fails
    """
    try:
        data: Dict[str, Any] = {"status": status}
        
        if status == "processing":
            data["startedAt"] = datetime.utcnow()
        elif status in ["completed", "failed"]:
            data["completedAt"] = datetime.utcnow()
        
        if error_message:
            data["errorMessage"] = error_message
        if result:
            data["result"] = result
        if used_provider:
            data["usedProvider"] = used_provider
        if used_model:
            data["usedModel"] = used_model
        if generation_time_ms:
            data["generationTimeMs"] = generation_time_ms
        if celery_task_id:
            data["celeryTaskId"] = celery_task_id
        
        job = await db.job.update(
            where={"id": job_id},
            data=data
        )
        logger.info("Job status updated", job_id=job_id, status=status)
        return job
    except Exception as e:
        logger.error("Failed to update job status", job_id=job_id, error=str(e))
        raise DatabaseError(f"Failed to update job status: {str(e)}")


async def delete_job(db: Any, job_id: str) -> None:
    """Delete job by ID.
    
    Args:
        db: Prisma client
        job_id: Job ID
        
    Raises:
        DatabaseError: If deletion fails
    """
    try:
        await db.job.delete(where={"id": job_id})
        logger.info("Job deleted", job_id=job_id)
    except Exception as e:
        logger.error("Failed to delete job", job_id=job_id, error=str(e))
        raise DatabaseError(f"Failed to delete job: {str(e)}")


async def get_job_stats(db: Any, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get job statistics.
    
    Args:
        db: Prisma client
        user_id: Filter by user ID
        
    Returns:
        Job statistics
    """
    try:
        where: Dict[str, Any] = {}
        if user_id:
            where["userId"] = user_id
            
        total = await db.job.count(where=where)
        
        statuses = ["queued", "processing", "completed", "failed", "cancelled"]
        by_status = {}
        for status in statuses:
            where_status = {**where, "status": status}
            by_status[status] = await db.job.count(where=where_status)
            
        completed = by_status.get("completed", 0)
        failed = by_status.get("failed", 0)
        success_rate = (completed / (completed + failed)) if (completed + failed) > 0 else 0
        
        # Average generation time for completed jobs
        avg_gen_time = 0
        completed_jobs = await db.job.find_many(
            where={**where, "status": "completed", "generationTimeMs": {"not": None}},
        )
        if completed_jobs:
            avg_gen_time = sum(j.generationTimeMs for j in completed_jobs if j.generationTimeMs) / len(completed_jobs)
            
        return {
            "total": total,
            "by_status": by_status,
            "success_rate": success_rate,
            "avg_generation_time_ms": avg_gen_time
        }
    except Exception as e:
        logger.error("Failed to get job stats", error=str(e))
        raise DatabaseError(f"Failed to get job stats: {str(e)}")


async def update_provider_health(
    db: Any,
    provider: str,
    status: str,
    error_message: Optional[str] = None,
    response_time_ms: Optional[int] = None,
    cost_per_request: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ProviderHealth:
    """Update provider health status.
    
    Args:
        db: Prisma client
        provider: Provider name
        status: Health status (healthy, degraded, unhealthy)
        error_message: Error message if unhealthy
        response_time_ms: Average response time
        cost_per_request: Cost per request
        metadata: Provider metadata
        
    Returns:
        Updated provider health
    """
    try:
        existing = await db.providerhealth.find_unique(where={"provider": provider})
        
        consecutive_failures = 0
        if existing:
            consecutive_failures = existing.consecutiveFailures + 1 if status == "unhealthy" else 0
        
        data: Dict[str, Any] = {
            "status": status,
            "lastCheckedAt": datetime.utcnow(),
            "consecutiveFailures": consecutive_failures,
        }
        
        if error_message:
            data["lastErrorMessage"] = error_message
        if response_time_ms:
            data["avgResponseTimeMs"] = response_time_ms
        if cost_per_request:
            data["costPerRequest"] = cost_per_request
        if metadata:
            data["metadata"] = metadata
        
        health = await db.providerhealth.upsert(
            where={"provider": provider},
            data={
                "create": {
                    "provider": provider,
                    **data
                },
                "update": data
            }
        )
        
        logger.info("Provider health updated", provider=provider, status=status)
        return health
    except Exception as e:
        logger.error("Failed to update provider health", provider=provider, error=str(e))
        raise DatabaseError(f"Failed to update provider health: {str(e)}")


async def get_provider_health(db: Any, provider: Optional[str] = None) -> List[ProviderHealth]:
    """Get provider health status.
    
    Args:
        db: Prisma client
        provider: Specific provider name (optional)
        
    Returns:
        List of provider health records
    """
    try:
        if provider:
            health = await db.providerhealth.find_unique(where={"provider": provider})
            return [health] if health else []
        else:
            return await db.providerhealth.find_many()
    except Exception as e:
        logger.error("Failed to get provider health", error=str(e))
        raise DatabaseError(f"Failed to get provider health: {str(e)}")


async def create_metric(
    db: Any,
    component: str,
    metric: str,
    value: float,
    job_id: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None
) -> Metric:
    """Create a metric record.
    
    Args:
        db: Prisma client
        component: Component name (api, worker, database, provider)
        metric: Metric name
        value: Metric value
        job_id: Associated job ID (optional)
        tags: Additional tags
        
    Returns:
        Created metric
    """
    try:
        return await db.metric.create(
            data={
                "component": component,
                "metric": metric,
                "value": value,
                "jobId": job_id,
                "tags": tags or {}
            }
        )
    except Exception as e:
        logger.error("Failed to create metric", error=str(e))
        raise DatabaseError(f"Failed to create metric: {str(e)}")
