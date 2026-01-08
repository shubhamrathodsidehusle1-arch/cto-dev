"""Text-to-video generation pipeline."""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from app.config import settings
from app.providers.manager import get_provider_manager
from app.providers.types import VideoGenerationParams, VideoGenerationRequest
from app.storage.service import get_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_public_video_url(job_id: str, download_token: str) -> str:
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/api/{settings.API_VERSION}/jobs/{job_id}/video?token={download_token}"


async def generate_video_for_job(
    *,
    job_id: str,
    user_id: str,
    prompt: str,
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate a video for a job.

    Args:
        job_id: Job ID.
        user_id: User ID.
        prompt: Prompt text.
        metadata: Job metadata that may include model/resolution/etc.

    Returns:
        Result payload stored in Job.result.

    Raises:
        Exception: If generation fails.
    """

    meta = metadata or {}
    params = VideoGenerationParams(
        resolution=str(meta.get("resolution") or "1080p"),
        duration_seconds=meta.get("duration"),
        quality=str(meta.get("quality") or "high"),
        style=meta.get("style"),
        mode=meta.get("mode") or "text-to-video",
        model=meta.get("model"),
    )

    provider_manager = get_provider_manager()
    selection = await provider_manager.select_provider(
        preferred_provider_id=meta.get("provider"),
        preferred_model_id=params.model,
        fallback_order=settings.PROVIDER_FALLBACK_ORDER,
    )

    provider = selection.provider

    start = time.time()
    request = VideoGenerationRequest(prompt=prompt, params=params, user_id=user_id, job_id=job_id)
    provider_result = await provider.generate_video(request)

    storage = get_storage()

    stored_path: Optional[str] = None
    stored_size: Optional[int] = None

    if provider_result.video_bytes is not None:
        stored = await storage.store_bytes(
            job_id=job_id,
            data=provider_result.video_bytes,
            extension="mp4",
            content_type="video/mp4",
            metadata={"provider": provider.provider_id, "model": params.model},
        )
        stored_path = stored.path
        stored_size = stored.size_bytes

    elif provider_result.video_url is not None:
        async with httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS) as client:
            resp = await client.get(provider_result.video_url)
            resp.raise_for_status()
            stored = await storage.store_bytes(
                job_id=job_id,
                data=resp.content,
                extension="mp4",
                content_type=resp.headers.get("content-type") or "video/mp4",
                metadata={"provider": provider.provider_id, "model": params.model},
            )
            stored_path = stored.path
            stored_size = stored.size_bytes

    else:
        raise ValueError("Provider did not return video bytes or a URL")

    generation_time_ms = int((time.time() - start) * 1000)
    download_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=settings.VIDEO_RETENTION_DAYS)

    result: Dict[str, Any] = {
        "videoUrl": _build_public_video_url(job_id, download_token),
        "downloadToken": download_token,
        "expiresAt": expires_at.isoformat() + "Z",
        "storagePath": stored_path,
        "sizeBytes": stored_size,
        "durationSeconds": provider_result.duration_seconds,
        "resolution": provider_result.resolution or params.resolution,
        "providerJobId": provider_result.provider_job_id,
        "providerRaw": provider_result.raw,
        "costUsd": provider_result.cost_usd,
        "generatedAt": datetime.utcnow().isoformat() + "Z",
    }

    logger.info(
        "Video generated",
        job_id=job_id,
        provider=provider.provider_id,
        model=params.model,
        generation_time_ms=generation_time_ms,
        size_bytes=stored_size,
    )

    return {
        "result": result,
        "used_provider": provider.provider_id,
        "used_model": params.model,
        "generation_time_ms": generation_time_ms,
    }
