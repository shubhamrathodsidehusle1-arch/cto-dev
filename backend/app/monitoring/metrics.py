"""Prometheus metrics configuration."""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

registry = CollectorRegistry()

job_completion_rate = Counter(
    "job_completion_rate",
    "Total number of completed jobs",
    ["status"],
    registry=registry,
)

job_processing_time_seconds = Histogram(
    "job_processing_time_seconds",
    "Time spent processing jobs",
    ["provider", "model"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],
    registry=registry,
)

job_queue_depth = Gauge(
    "job_queue_depth", "Number of jobs in queue", ["queue_name"], registry=registry
)

provider_health_status = Gauge(
    "provider_health_status",
    "Provider health status (1=healthy, 0.5=degraded, 0=unhealthy)",
    ["provider"],
    registry=registry,
)

api_request_duration_seconds = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)


def record_job_completion(status: str) -> None:
    """Record job completion.

    Args:
        status: Job status (completed or failed)
    """
    job_completion_rate.labels(status=status).inc()


def record_job_processing_time(
    duration_seconds: float, provider: str, model: str
) -> None:
    """Record job processing time.

    Args:
        duration_seconds: Processing duration in seconds
        provider: Provider name
        model: Model name
    """
    job_processing_time_seconds.labels(provider=provider, model=model).observe(
        duration_seconds
    )


def update_queue_depth(queue_name: str, depth: int) -> None:
    """Update queue depth metric.

    Args:
        queue_name: Queue name
        depth: Number of jobs in queue
    """
    job_queue_depth.labels(queue_name=queue_name).set(depth)


def update_provider_health(provider: str, status: str) -> None:
    """Update provider health metric.

    Args:
        provider: Provider name
        status: Health status (healthy, degraded, unhealthy)
    """
    status_value = {
        "healthy": 1.0,
        "degraded": 0.5,
        "unhealthy": 0.0,
        "unknown": -1.0,
    }.get(status, -1.0)

    provider_health_status.labels(provider=provider).set(status_value)


def record_api_request(
    method: str, endpoint: str, status_code: int, duration_seconds: float
) -> None:
    """Record API request duration.

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
        duration_seconds: Request duration in seconds
    """
    api_request_duration_seconds.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).observe(duration_seconds)
