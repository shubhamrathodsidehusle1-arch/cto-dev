"""Provider manager.

The ProviderManager is responsible for:
- Registering providers
- Selecting an available provider/model
- Performing health checks
- Applying simple per-provider rate limiting

It is deliberately lightweight; higher-level orchestration is implemented in the
video pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.providers.base import AIProvider
from app.providers.openrouter import OpenRouterProvider
from app.providers.mock import MockProvider
from app.providers.types import ProviderHealth, ProviderModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderSelection:
    """Resolved provider + optional model."""

    provider: AIProvider
    model_id: Optional[str] = None


class SimpleTokenBucket:
    """In-memory token bucket rate limiter."""

    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def consume(self, amount: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class ProviderManager:
    """Registry and selection logic for providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, AIProvider] = {}
        self._rate_limits: Dict[str, SimpleTokenBucket] = {}

        self.register(OpenRouterProvider())
        self.register(MockProvider())

    def register(self, provider: AIProvider, requests_per_minute: int = 60) -> None:
        """Register a provider implementation."""

        self._providers[provider.provider_id] = provider
        self._rate_limits[provider.provider_id] = SimpleTokenBucket(
            capacity=requests_per_minute,
            refill_per_second=requests_per_minute / 60.0,
        )

    def list_provider_ids(self) -> List[str]:
        return sorted(self._providers.keys())

    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        return self._providers.get(provider_id)

    async def list_models(self, provider_id: str) -> List[ProviderModel]:
        provider = self.get_provider(provider_id)
        if not provider:
            return []
        return await provider.list_models()

    async def health_check(
        self,
        provider_id: str,
        timeout_seconds: int = 10,
    ) -> Optional[ProviderHealth]:
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        return await provider.health_check(timeout_seconds=timeout_seconds)

    def _is_rate_limited(self, provider_id: str) -> bool:
        limiter = self._rate_limits.get(provider_id)
        if not limiter:
            return False
        return not limiter.consume(1.0)

    async def select_provider(
        self,
        preferred_provider_id: Optional[str] = None,
        preferred_model_id: Optional[str] = None,
        fallback_order: Optional[List[str]] = None,
    ) -> ProviderSelection:
        """Select a provider using health checks and fallback order."""

        order: List[str] = []
        if preferred_provider_id:
            order.append(preferred_provider_id)
        if fallback_order:
            order.extend([p for p in fallback_order if p not in order])
        # Default fallback: all registered providers.
        order.extend([p for p in self.list_provider_ids() if p not in order])

        for provider_id in order:
            provider = self.get_provider(provider_id)
            if not provider:
                continue
            if self._is_rate_limited(provider_id):
                logger.warning("Provider rate limited", provider=provider_id)
                continue
            health = await provider.health_check(timeout_seconds=5)
            if health.status != "healthy":
                continue
            return ProviderSelection(provider=provider, model_id=preferred_model_id)

        # Always fallback to mock (guaranteed registered)
        return ProviderSelection(provider=self._providers["mock"], model_id=preferred_model_id)


_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """Get a singleton ProviderManager."""

    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager
