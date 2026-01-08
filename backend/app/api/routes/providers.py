"""Provider API routes."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.api.models.provider import (
    ProviderHealthResponse,
    ProviderInfoResponse,
    ProviderModelResponse,
    ProviderTestRequest,
)
from app.db.models import get_provider_health, update_provider_health
from app.db.prisma import get_prisma
from app.providers.manager import get_provider_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=List[ProviderInfoResponse])
async def list_providers() -> List[ProviderInfoResponse]:
    """List configured providers."""

    pm = get_provider_manager()
    return [ProviderInfoResponse(id=pid, name=pid) for pid in pm.list_provider_ids()]


@router.get("/status", response_model=List[ProviderHealthResponse])
async def get_provider_status() -> List[ProviderHealthResponse]:
    """Get health status of all providers recorded in the database."""

    db = await get_prisma()
    providers = await get_provider_health(db=db)
    return [ProviderHealthResponse.model_validate(p) for p in providers]


@router.get("/{provider_id}/health", response_model=ProviderHealthResponse)
async def get_provider_health_endpoint(provider_id: str) -> ProviderHealthResponse:
    """Run a live health check for a provider and persist the result."""

    pm = get_provider_manager()
    provider = pm.get_provider(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    health = await provider.health_check(timeout_seconds=10)

    db = await get_prisma()
    record = await update_provider_health(
        db=db,
        provider=provider_id,
        status=health.status,
        error_message=health.error_message,
        response_time_ms=health.response_time_ms,
        metadata=health.metadata,
    )

    return ProviderHealthResponse.model_validate(record)


@router.get("/{provider_id}/models", response_model=List[ProviderModelResponse])
async def list_provider_models(provider_id: str) -> List[ProviderModelResponse]:
    """List models available for a provider."""

    pm = get_provider_manager()
    provider = pm.get_provider(provider_id)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    models = await provider.list_models()
    return [
        ProviderModelResponse(
            id=m.id,
            name=m.name,
            modes=m.modes,
            max_duration_seconds=m.max_duration_seconds,
            max_resolution=m.max_resolution,
        )
        for m in models
    ]


@router.post("/test", response_model=ProviderHealthResponse)
async def test_provider(test_request: ProviderTestRequest) -> ProviderHealthResponse:
    """Test a specific provider and update its health status."""

    pm = get_provider_manager()
    provider = pm.get_provider(test_request.provider)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    logger.info("Testing provider", provider=test_request.provider)

    health = await provider.health_check(timeout_seconds=test_request.timeout)

    db = await get_prisma()
    record = await update_provider_health(
        db=db,
        provider=test_request.provider,
        status=health.status,
        error_message=health.error_message,
        response_time_ms=health.response_time_ms,
        metadata=health.metadata,
    )

    return ProviderHealthResponse.model_validate(record)
