"""Job API models."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Job creation request."""
    userId: str = Field(..., description="User ID")
    prompt: str = Field(..., min_length=1, max_length=5000, description="Video generation prompt")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    maxRetries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")


class JobResponse(BaseModel):
    """Job response model."""
    id: str
    userId: str
    status: str
    prompt: str
    metadata: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    startedAt: Optional[datetime]
    completedAt: Optional[datetime]
    retryCount: int
    maxRetries: int
    celeryTaskId: Optional[str] = None
    usedProvider: Optional[str]
    usedModel: Optional[str]
    generationTimeMs: Optional[int]
    errorMessage: Optional[str]
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class JobListResponse(BaseModel):
    """Job list response."""
    jobs: list[JobResponse]
    total: int
    skip: int
    take: int


class JobStatusUpdate(BaseModel):
    """Job status update request."""
    status: str = Field(..., pattern="^(queued|processing|completed|failed|cancelled)$")
    errorMessage: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class JobStatsResponse(BaseModel):
    """Job statistics response."""
    total: int
    by_status: Dict[str, int]
    success_rate: float
    avg_generation_time_ms: Optional[float]
