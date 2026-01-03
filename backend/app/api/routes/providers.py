"""Provider API routes."""
from typing import List
from fastapi import APIRouter

from app.api.models.provider import ProviderHealthResponse, ProviderTestRequest
from app.db.prisma import get_prisma
from app.db.models import get_provider_health, update_provider_health
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status", response_model=List[ProviderHealthResponse])
async def get_provider_status() -> List[ProviderHealthResponse]:
    """Get health status of all providers.
    
    Returns:
        List of provider health statuses
    """
    db = await get_prisma()
    
    providers = await get_provider_health(db=db)
    
    return [ProviderHealthResponse.model_validate(p) for p in providers]


@router.post("/test", response_model=ProviderHealthResponse)
async def test_provider(test_request: ProviderTestRequest) -> ProviderHealthResponse:
    """Test a specific provider and update its health status.
    
    Args:
        test_request: Provider test request
        
    Returns:
        Updated provider health status
    """
    db = await get_prisma()
    
    logger.info("Testing provider", provider=test_request.provider)
    
    # Get existing metadata if any
    existing_health = await db.providerhealth.find_unique(where={"provider": test_request.provider})
    metadata = existing_health.metadata if existing_health else None
    
    try:
        # Mock test logic
        status = "healthy"
        error_message = None
        response_time_ms = 100
    except Exception as e:
        logger.error("Provider test failed", provider=test_request.provider, error=str(e))
        status = "unhealthy"
        error_message = str(e)
        response_time_ms = None
    
    health = await update_provider_health(
        db=db,
        provider=test_request.provider,
        status=status,
        error_message=error_message,
        response_time_ms=response_time_ms,
        metadata=metadata
    )
    
    return ProviderHealthResponse.model_validate(health)
