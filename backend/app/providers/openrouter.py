"""OpenRouter provider implementation.

OpenRouter offers an OpenAI-compatible API surface for accessing many models.
This implementation focuses on model discovery and a best-effort video generation
API wrapper (provider-specific details depend on the underlying model).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.providers.base import AIProvider
from app.providers.types import (
    ProviderHealth,
    ProviderModel,
    VideoGenerationRequest,
    VideoGenerationResult,
)


class OpenRouterProvider(AIProvider):
    """OpenRouter provider."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")

    @property
    def provider_id(self) -> str:
        return "openrouter"

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def list_models(self) -> List[ProviderModel]:
        if not self._api_key:
            return []

        url = f"{self._base_url}/models"
        async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            payload = resp.json()

        models: List[ProviderModel] = []
        for m in payload.get("data", []):
            model_id = m.get("id")
            if not model_id:
                continue
            models.append(
                ProviderModel(
                    id=model_id,
                    name=m.get("name") or model_id,
                    modes=["text-to-video"],
                )
            )
        return models

    async def health_check(self, timeout_seconds: int = 10) -> ProviderHealth:
        start = time.time()
        if not self._api_key:
            return ProviderHealth(
                provider=self.provider_id,
                status="unhealthy",
                error_message="OPENROUTER_API_KEY not configured",
                response_time_ms=None,
            )

        url = f"{self._base_url}/models"
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.get(url, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()

            duration_ms = int((time.time() - start) * 1000)
            model_ids = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return ProviderHealth(
                provider=self.provider_id,
                status="healthy",
                response_time_ms=duration_ms,
                metadata={"models": model_ids[:50]},
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return ProviderHealth(
                provider=self.provider_id,
                status="unhealthy",
                response_time_ms=duration_ms,
                error_message=str(e),
            )

    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """Generate a video via OpenRouter.

        OpenRouter does not provide a single unified video-generation endpoint.
        For now, this method attempts to call an OpenAI-compatible endpoint that
        some video-capable models expose. If that fails, callers should rely on a
        fallback provider.
        """

        if not self._api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        model = request.params.model or settings.OPENROUTER_DEFAULT_VIDEO_MODEL
        if not model:
            raise ValueError("No OpenRouter model configured")

        url = f"{self._base_url}/chat/completions"
        body: Dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a video generation API. If you can generate a video, "
                        "return ONLY a JSON object with keys: video_url (public URL), "
                        "duration_seconds (int), resolution (string)."
                    ),
                },
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, headers=self._headers(), json=body)
            resp.raise_for_status()
            payload = resp.json()

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        if not isinstance(content, str):
            raise ValueError("Unexpected OpenRouter response")

        # Best-effort parsing: expect raw JSON in the content.
        import json

        try:
            parsed = json.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to parse model output as JSON: {e}")

        video_url = parsed.get("video_url")
        if not video_url:
            raise ValueError("Model did not provide video_url")

        return VideoGenerationResult(
            video_url=video_url,
            duration_seconds=parsed.get("duration_seconds"),
            resolution=parsed.get("resolution"),
            provider_job_id=None,
            raw={"openrouter": payload},
        )
