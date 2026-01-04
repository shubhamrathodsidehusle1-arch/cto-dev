"""Custom error definitions."""
from typing import Any, Optional


class APIError(Exception):
    """Base API error."""

    def __init__(
        self, message: str, status_code: int = 500, details: Optional[Any] = None
    ):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class JobNotFoundError(APIError):
    """Job not found error."""

    def __init__(self, job_id: str):
        """Initialize job not found error.

        Args:
            job_id: Job ID that was not found
        """
        super().__init__(message=f"Job {job_id} not found", status_code=404)


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Any] = None):
        """Initialize validation error.

        Args:
            message: Error message
            details: Validation details
        """
        super().__init__(message=message, status_code=400, details=details)


class ProviderError(APIError):
    """Provider error."""

    def __init__(self, provider: str, message: str):
        """Initialize provider error.

        Args:
            provider: Provider name
            message: Error message
        """
        super().__init__(
            message=f"Provider {provider} error: {message}", status_code=503
        )


class DatabaseError(APIError):
    """Database error."""

    def __init__(self, message: str):
        """Initialize database error.

        Args:
            message: Error message
        """
        super().__init__(message=f"Database error: {message}", status_code=500)
