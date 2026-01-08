"""Application configuration."""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "ai-video-generation-backend"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_VERSION: str = "v1"
    LOG_LEVEL: str = "INFO"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ai_video_generation"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TIME_LIMIT: int = 4000
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3600
    CELERY_MAX_RETRIES: int = 3
    CELERY_RETRY_BACKOFF: int = 60
    
    # Security
    SECRET_KEY: str = "development-secret-key-change-in-production"
    API_KEY: str = "development-api-key-change-in-production"
    JWT_SECRET_KEY: str = "development-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_HASH_ROUNDS: int = 12
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Task Queue Configuration
    DEFAULT_QUEUE_NAME: str = "default"
    HIGH_PRIORITY_QUEUE_NAME: str = "high_priority"
    LOW_PRIORITY_QUEUE_NAME: str = "low_priority"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True


settings = Settings()
