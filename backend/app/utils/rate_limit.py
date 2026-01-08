"""Rate limiting utilities.

Rate limiting is best-effort: if Redis is unavailable, requests are allowed.
"""

from __future__ import annotations

from typing import Optional

import redis

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def check_rate_limit(*, key: str, limit: int, window_seconds: int) -> Optional[int]:
    """Check and increment a rate limit counter.

    Args:
        key: Unique rate limit key.
        limit: Maximum allowed requests per window.
        window_seconds: Window size in seconds.

    Returns:
        Remaining requests in the current window if Redis is available, otherwise None.

    Raises:
        ValueError: If over limit.
    """

    try:
        client = redis.from_url(settings.REDIS_URL)
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        current, ttl = pipe.execute()

        if ttl == -1:
            client.expire(key, window_seconds)
            ttl = window_seconds

        if current > limit:
            raise ValueError("Rate limit exceeded")

        remaining = max(0, limit - int(current))
        return remaining
    except ValueError:
        raise
    except Exception as e:
        logger.warning("Rate limit check failed; allowing request", key=key, error=str(e))
        return None
