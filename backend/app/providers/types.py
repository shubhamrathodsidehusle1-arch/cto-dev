"""Provider type definitions.

The provider layer is intentionally provider-agnostic to allow swapping between
multiple AI vendors and models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

ProviderHealthStatus = Literal["healthy", "degraded", "unhealthy", "unknown"]
GenerationStatus = Literal["queued", "processing", "completed", "failed", "cancelled"]
GenerationMode = Literal["text-to-video", "image-to-video", "video-to-video"]


@dataclass(frozen=True)
class ProviderModel:
    """A provider model and its capabilities."""

    id: str
    name: str
    modes: List[GenerationMode]
    max_duration_seconds: Optional[int] = None
    max_resolution: Optional[str] = None


@dataclass(frozen=True)
class ProviderHealth:
    """Health information for a provider."""

    provider: str
    status: ProviderHealthStatus
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class VideoGenerationParams:
    """Video generation parameters."""

    resolution: str = "1080p"
    duration_seconds: Optional[int] = None
    quality: str = "high"
    style: Optional[str] = None
    mode: GenerationMode = "text-to-video"
    model: Optional[str] = None


@dataclass(frozen=True)
class VideoGenerationRequest:
    """A provider-agnostic video generation request."""

    prompt: str
    params: VideoGenerationParams
    user_id: str
    job_id: str


@dataclass(frozen=True)
class VideoGenerationResult:
    """The final result of a video generation."""

    video_bytes: Optional[bytes] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    resolution: Optional[str] = None
    provider_job_id: Optional[str] = None
    cost_usd: Optional[float] = None
    raw: Optional[Dict[str, Any]] = None
