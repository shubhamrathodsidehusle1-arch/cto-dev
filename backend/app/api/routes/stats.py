"""Stats API routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from prisma.models import User

from app.api.dependencies import get_current_user
from app.api.models.job import JobStatsResponse
from app.api.models.provider import ProviderHealthResponse
from app.db.models import get_job_stats, get_provider_health
from app.db.prisma import get_prisma

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/providers", response_model=List[ProviderHealthResponse])
async def get_provider_stats(
    current_user: User = Depends(get_current_user),
) -> List[ProviderHealthResponse]:
    """Get provider health records.

    Args:
        current_user: Current user (auth required).

    Returns:
        Provider health list.
    """

    db = await get_prisma()
    providers = await get_provider_health(db=db)
    return [ProviderHealthResponse.model_validate(p) for p in providers]


@router.get("/jobs", response_model=JobStatsResponse)
async def get_job_stats_endpoint(
    current_user: User = Depends(get_current_user),
) -> JobStatsResponse:
    """Get job generation statistics for the current user."""

    db = await get_prisma()
    stats = await get_job_stats(db=db, user_id=current_user.id)
    return JobStatsResponse(**stats)


@router.get("/summary")
async def get_summary(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get overall summary stats for the current user."""

    db = await get_prisma()
    providers = await get_provider_health(db=db)
    jobs = await get_job_stats(db=db, user_id=current_user.id)
    return {
        "providers": [ProviderHealthResponse.model_validate(p) for p in providers],
        "jobs": jobs,
    }
