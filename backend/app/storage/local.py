"""Local filesystem storage implementation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings
from app.storage.base import VideoStorage
from app.storage.types import StoredVideo


class LocalVideoStorage(VideoStorage):
    """Stores videos on the local filesystem."""

    def __init__(self, base_path: Optional[str] = None) -> None:
        self._base_path = Path(base_path or settings.VIDEO_STORAGE_PATH).expanduser().resolve()
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _job_dir(self, job_id: str) -> Path:
        # Shard by first two chars to avoid too many files in one directory.
        shard = job_id[:2] if len(job_id) >= 2 else "xx"
        job_dir = self._base_path / shard / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    async def store_bytes(
        self,
        *,
        job_id: str,
        data: bytes,
        extension: str = "mp4",
        content_type: str = "video/mp4",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredVideo:
        job_dir = self._job_dir(job_id)
        filename = f"result.{extension.lstrip('.')}"
        path = job_dir / filename
        path.write_bytes(data)

        rel_path = str(path.relative_to(self._base_path))
        return StoredVideo(
            path=rel_path,
            size_bytes=path.stat().st_size,
            content_type=content_type,
            created_at=datetime.utcnow(),
            metadata=metadata,
        )

    def get_absolute_path(self, stored_path: str) -> str:
        return str((self._base_path / stored_path).resolve())
