"""Metadata API routes."""
from typing import List
from fastapi import APIRouter, HTTPException

from app.api.models.metadata import SystemMetadataResponse, SystemMetadataListResponse
from app.db.prisma import get_prisma
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("", response_model=SystemMetadataListResponse)
async def get_all_metadata() -> SystemMetadataListResponse:
    """Get all system metadata.

    Returns:
        List of all system metadata
    """
    db = await get_prisma()
    metadata = await db.systemmetadata.find_many()
    return SystemMetadataListResponse(
        metadata=[SystemMetadataResponse.model_validate(m) for m in metadata]
    )


@router.get("/{key}", response_model=SystemMetadataResponse)
async def get_metadata_by_key(key: str) -> SystemMetadataResponse:
    """Get system metadata by key.

    Args:
        key: Metadata key

    Returns:
        System metadata details

    Raises:
        HTTPException: If metadata not found
    """
    db = await get_prisma()
    metadata = await db.systemmetadata.find_unique(where={"key": key})

    if not metadata:
        raise HTTPException(
            status_code=404, detail=f"Metadata with key '{key}' not found"
        )

    return SystemMetadataResponse.model_validate(metadata)
