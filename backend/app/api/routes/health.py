"""Health check routes."""
from typing import Dict, Any
from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.monitoring.health import get_system_health
from app.monitoring.metrics import registry

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness_probe() -> Dict[str, str]:
    """Liveness probe for container orchestration.
    
    Returns:
        Liveness status
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """Readiness probe for container orchestration.
    
    Returns:
        Readiness status with component health
    """
    health = await get_system_health()
    return health


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint.
    
    Returns:
        Prometheus metrics in text format
    """
    metrics_data = generate_latest(registry)
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
