"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.prisma import get_prisma, disconnect_prisma
from app.api.routes import jobs, health, providers
from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.api.middleware.request_validation import RequestValidationMiddleware
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler.
    
    Args:
        app: FastAPI application
        
    Yields:
        None
    """
    logger.info("Starting application", app_name=settings.APP_NAME, env=settings.APP_ENV)
    
    await get_prisma()
    logger.info("Database connected")
    
    yield
    
    await disconnect_prisma()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="AI Video Generation Backend",
    description="Production-ready backend for AI video generation platform",
    version="0.1.0",
    lifespan=lifespan
)

app.state.config = settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestValidationMiddleware)

app.include_router(health.router)
app.include_router(jobs.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(providers.router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/")
async def root():
    """Root endpoint.
    
    Returns:
        Welcome message
    """
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "env": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
