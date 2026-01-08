"""Storage interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.storage.types import StoredVideo


class VideoStorage(ABC):
    """Abstract interface for video storage."""

    @abstractmethod
    async def store_bytes(
        self,
        *,
        job_id: str,
        data: bytes,
        extension: str = "mp4",
        content_type: str = "video/mp4",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredVideo:
        """Store a video from bytes."""

    @abstractmethod
    def get_absolute_path(self, stored_path: str) -> str:
        """Resolve a stored path to an absolute filesystem path."""
