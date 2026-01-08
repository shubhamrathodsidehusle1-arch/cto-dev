"""Mock provider implementation.

This provider is used for local development and as a fallback when real
providers are unavailable.
"""

from __future__ import annotations

import asyncio
import secrets
from typing import List

from app.providers.base import AIProvider
from app.providers.types import (
    ProviderHealth,
    ProviderModel,
    VideoGenerationRequest,
    VideoGenerationResult,
)


# Minimal MP4 header used as a placeholder file.
_PLACEHOLDER_MP4 = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


class MockProvider(AIProvider):
    """Mock provider that returns a small placeholder MP4 file."""

    @property
    def provider_id(self) -> str:
        return "mock"

    async def list_models(self) -> List[ProviderModel]:
        return [
            ProviderModel(
                id="mock-video-1",
                name="Mock Video Model",
                modes=["text-to-video"],
                max_duration_seconds=60,
                max_resolution="1080p",
            )
        ]

    async def health_check(self, timeout_seconds: int = 10) -> ProviderHealth:
        return ProviderHealth(
            provider=self.provider_id,
            status="healthy",
            response_time_ms=1,
            metadata={"models": ["mock-video-1"]},
        )

    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        await asyncio.sleep(0.5)

        provider_job_id = f"mock_{secrets.token_hex(8)}"

        return VideoGenerationResult(
            video_bytes=_PLACEHOLDER_MP4,
            duration_seconds=request.params.duration_seconds or 10,
            resolution=request.params.resolution,
            provider_job_id=provider_job_id,
            cost_usd=0.0,
            raw={"provider": self.provider_id},
        )
