"""Storage layer type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class StoredVideo:
    """Information about a stored video object."""

    path: str
    size_bytes: int
    content_type: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
