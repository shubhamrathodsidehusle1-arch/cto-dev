"""Job API models."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Job creation request."""
    prompt: str = Field(..., min_length=1, max_length=5000, description="Video generation prompt")
    projectId: Optional[str] = Field(None, description="Project ID (optional)")
    model: Optional[str] = Field(None, description="AI model to use")
    resolution: Optional[str] = Field("1080p", description="Video resolution (e.g., 1080p, 720p, 4k)")
    quality: Optional[str] = Field("high", description="Video quality (e.g., high, medium, low)")
    duration: Optional[int] = Field(None, ge=1, le=60, description="Video duration in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    maxRetries: Optional[int] = Field(default=None, ge=0, le=10, description="Maximum retry attempts")


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
