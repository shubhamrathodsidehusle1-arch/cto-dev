"""Error handling middleware."""
from typing import Callable
import time
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.errors import APIError
from app.utils.logger import get_logger
from app.monitoring.metrics import record_api_request

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and logging requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request and errors.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        start_time = time.time()

        try:
            response = await call_next(request)

            duration = time.time() - start_time

            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration,
            )

            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            return response

        except APIError as e:
            duration = time.time() - start_time

            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=e.status_code,
                duration_seconds=duration,
            )

            logger.error(
                "API error",
                method=request.method,
                path=request.url.path,
                status_code=e.status_code,
                error=e.message,
                details=e.details,
            )

            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.message, "details": e.details},
            )

        except Exception as e:
            duration = time.time() - start_time

            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration_seconds=duration,
            )

            logger.error(
                "Unexpected error",
                method=request.method,
                path=request.url.path,
                error=str(e),
                traceback=traceback.format_exc(),
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "details": str(e) if request.app.state.config.APP_DEBUG else None,
                },
            )
