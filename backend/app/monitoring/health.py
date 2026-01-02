"""Health check utilities."""
from typing import Dict, Any
import time

from app.db.prisma import get_prisma
from app.config import settings
from app.utils.logger import get_logger
import redis

logger = get_logger(__name__)


async def check_database_health() -> Dict[str, Any]:
    """Check database health.
    
    Returns:
        Health status dict
    """
    try:
        db = await get_prisma()
        await db.query_raw("SELECT 1")
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health.
    
    Returns:
        Health status dict
    """
    try:
        client = redis.from_url(settings.REDIS_URL)
        start = time.time()
        client.ping()
        latency_ms = (time.time() - start) * 1000
        client.close()
        return {"status": "healthy", "latency_ms": round(latency_ms, 2)}
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


async def get_system_health() -> Dict[str, Any]:
    """Get overall system health.
    
    Returns:
        System health status
    """
    database_health = await check_database_health()
    redis_health = await check_redis_health()
    
    is_healthy = (
        database_health["status"] == "healthy" and
        redis_health["status"] == "healthy"
    )
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "components": {
            "database": database_health,
            "redis": redis_health
        }
    }
