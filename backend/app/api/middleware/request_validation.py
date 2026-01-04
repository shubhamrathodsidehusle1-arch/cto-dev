"""Request validation middleware."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating requests."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Validate request.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response

        Raises:
            HTTPException: If validation fails
        """
        if request.url.path.startswith("/api/"):
            api_key = request.headers.get("X-API-Key")

            if not api_key and settings.APP_ENV == "production":
                logger.warning("Missing API key", path=request.url.path)
                raise HTTPException(status_code=401, detail="API key required")

            if (
                api_key
                and api_key != settings.API_KEY
                and settings.APP_ENV == "production"
            ):
                logger.warning("Invalid API key", path=request.url.path)
                raise HTTPException(status_code=403, detail="Invalid API key")

        response = await call_next(request)
        return response
