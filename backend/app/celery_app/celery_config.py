"""Celery configuration."""
from celery import Celery
from kombu import Queue, Exchange

from app.config import settings

celery_app = Celery(
    "ai_video_generation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

default_exchange = Exchange("default", type="direct")
high_priority_exchange = Exchange("high_priority", type="direct")
low_priority_exchange = Exchange("low_priority", type="direct")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    task_queues=(
        Queue(
            settings.DEFAULT_QUEUE_NAME,
            exchange=default_exchange,
            routing_key="default"
        ),
        Queue(
            settings.HIGH_PRIORITY_QUEUE_NAME,
            exchange=high_priority_exchange,
            routing_key="high_priority"
        ),
        Queue(
            settings.LOW_PRIORITY_QUEUE_NAME,
            exchange=low_priority_exchange,
            routing_key="low_priority"
        ),
    ),
    
    task_default_queue=settings.DEFAULT_QUEUE_NAME,
    task_default_exchange="default",
    task_default_routing_key="default",
    
    task_routes={
        "app.celery_app.tasks.process_video_generation": {
            "queue": settings.DEFAULT_QUEUE_NAME
        }
    },
    
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    result_expires=86400,
    
    task_annotations={
        "*": {
            "max_retries": settings.CELERY_MAX_RETRIES,
            "retry_backoff": settings.CELERY_RETRY_BACKOFF,
            "retry_backoff_max": 3600,
            "retry_jitter": True
        }
    }
)

celery_app.autodiscover_tasks(["app.celery_app"])
