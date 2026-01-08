"""Storage service factory."""

from __future__ import annotations

from typing import Optional

from app.storage.base import VideoStorage
from app.storage.local import LocalVideoStorage

_storage: Optional[VideoStorage] = None


def get_storage() -> VideoStorage:
    """Get a singleton storage backend."""

    global _storage
    if _storage is None:
        _storage = LocalVideoStorage()
    return _storage
