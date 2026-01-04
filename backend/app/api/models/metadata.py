"""Metadata API models."""
from typing import Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class SystemMetadataResponse(BaseModel):
    """System metadata response model."""

    key: str
    value: Any
    description: Optional[str]
    updatedAt: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SystemMetadataListResponse(BaseModel):
    """System metadata list response."""

    metadata: List[SystemMetadataResponse]
