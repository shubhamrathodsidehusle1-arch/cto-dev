"""Structured logging configuration."""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.config import settings


class StructuredLogger:
    """Structured logger with JSON output."""
    
    def __init__(self, name: str):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def _format_message(self, level: str, message: str, **kwargs: Any) -> str:
        """Format log message as JSON.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields
            
        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
        }
        log_data.update(kwargs)
        return json.dumps(log_data)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.error(self._format_message("ERROR", message, **kwargs))
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
