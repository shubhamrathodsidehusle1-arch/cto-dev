"""Provider API models."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProviderHealthResponse(BaseModel):
    """Provider health response model."""

    id: str
    provider: str
    status: str
    lastCheckedAt: datetime
    lastErrorMessage: Optional[str]
    consecutiveFailures: int
    avgResponseTimeMs: Optional[int]
    costPerRequest: Optional[float]
    metadata: Optional[dict] = None
    updatedAt: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class ProviderTestRequest(BaseModel):
    """Provider test request."""

    provider: str = Field(..., description="Provider name to test")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
