"""Provider interface.

Providers implement the methods below to integrate with the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.providers.types import (
    ProviderHealth,
    ProviderModel,
    VideoGenerationRequest,
    VideoGenerationResult,
)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Stable provider identifier."""

    @property
    def display_name(self) -> str:
        """Human friendly provider name."""

        return self.provider_id

    @abstractmethod
    async def list_models(self) -> List[ProviderModel]:
        """List models supported by this provider."""

    @abstractmethod
    async def health_check(self, timeout_seconds: int = 10) -> ProviderHealth:
        """Perform a health check for this provider."""

    @abstractmethod
    async def generate_video(
        self,
        request: VideoGenerationRequest,
    ) -> VideoGenerationResult:
        """Generate a video.

        Implementations may return either raw bytes (preferred for local storage)
        or a provider-hosted URL.
        """

    def supports_model(self, model_id: Optional[str]) -> bool:
        """Return True if this provider supports the requested model.

        Args:
            model_id: Model identifier.

        Returns:
            True if supported.
        """

        if model_id is None:
            return True
        return True
