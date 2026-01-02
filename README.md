# AI Video Generation Backend - Phase 1

Production-ready backend foundation for an AI video generation platform with FastAPI, Celery, PostgreSQL, and comprehensive monitoring.

## 🏗️ Architecture Overview

### Core Components

- **API Service**: FastAPI with async endpoints, request validation, and structured logging
- **Task Queue**: Celery with Redis broker for async video generation jobs
- **Database**: PostgreSQL with Prisma ORM for job tracking and telemetry
- **Monitoring**: Prometheus metrics and health endpoints
- **Orchestration**: Docker Compose for local development

### Tech Stack

- **Python 3.11+**
- **FastAPI 0.104+** - Modern async web framework
- **Celery 5.3+** - Distributed task queue
- **PostgreSQL 15+** - Relational database
- **Redis** - Message broker and cache
- **Prisma** - Next-generation ORM
- **Prometheus** - Metrics and monitoring

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd <repository-name>
```

2. **Set up environment variables**

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration if needed
```

3. **Start all services with Docker Compose**

```bash
cd ..
docker-compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI API (port 8000)
- Celery Worker
- Prometheus (port 9090)

4. **Verify the services are running**

```bash
# Check API health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/health/ready

# Check metrics
curl http://localhost:8000/metrics

# Access API docs
open http://localhost:8000/docs
```

## 📚 API Documentation

### Base URL

```
http://localhost:8000
```

### Endpoints

#### Jobs

- **POST /api/v1/jobs** - Create a new video generation job
  ```json
  {
    "userId": "user-123",
    "prompt": "Create a video of a sunset over the ocean",
    "metadata": {"priority": "high"},
    "maxRetries": 3
  }
  ```

- **GET /api/v1/jobs/{job_id}** - Get job status and details
- **GET /api/v1/jobs** - List jobs with filters and pagination
  - Query params: `userId`, `status`, `skip`, `take`
- **DELETE /api/v1/jobs/{job_id}** - Cancel/delete a job

#### Providers

- **GET /api/v1/providers/status** - Get health status of all providers
- **POST /api/v1/providers/test** - Test a specific provider
  ```json
  {
    "provider": "provider-name",
    "timeout": 30
  }
  ```

#### Health & Monitoring

- **GET /health** - Liveness probe (returns `{"status": "alive"}`)
- **GET /health/ready** - Readiness probe with component health
- **GET /metrics** - Prometheus metrics endpoint

### Interactive API Documentation

FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🗄️ Database Schema

### Jobs Table

Stores video generation job information with tracking fields:

- `id` (CUID) - Unique job identifier
- `userId` - User who created the job
- `status` - Current status (queued, processing, completed, failed)
- `prompt` - Video generation prompt
- `metadata` - JSON metadata
- `result` - JSON result with video URLs
- `retryCount` / `maxRetries` - Retry tracking
- `usedProvider` / `usedModel` - Provider/model used
- `generationTimeMs` - Processing time
- `errorMessage` - Error details if failed
- Timestamps: `createdAt`, `updatedAt`, `startedAt`, `completedAt`

### Provider Health Table

Tracks health and performance of video generation providers:

- `provider` - Provider name (unique)
- `status` - Health status (healthy, degraded, unhealthy)
- `lastCheckedAt` - Last health check timestamp
- `consecutiveFailures` - Failure count
- `avgResponseTimeMs` - Average response time
- `costPerRequest` - Cost tracking

### Metrics Table

Stores telemetry and performance metrics:

- `component` - Component name (api, worker, database, provider)
- `metric` - Metric name
- `value` - Metric value
- `tags` - Additional tags as JSON
- `jobId` - Associated job (optional)

## 🔄 Task Queue

### Queue Configuration

Three priority queues for job processing:

- **high_priority** - Critical/urgent jobs
- **default** - Standard jobs
- **low_priority** - Background/batch jobs

### Retry Policy

- **Max retries**: 3 attempts
- **Backoff**: Exponential with base delay of 60s
- **Max backoff**: 3600s (1 hour)
- **Jitter**: Enabled to prevent thundering herd

### Task Timeouts

- **Soft limit**: 3600s (1 hour) - sends exception
- **Hard limit**: 4000s - kills task

## 📊 Monitoring & Metrics

### Prometheus Metrics

Available at `/metrics`:

- `job_completion_rate` - Job completions by status
- `job_processing_time_seconds` - Processing duration histogram
- `job_queue_depth` - Jobs in queue by queue name
- `provider_health_status` - Provider health (1=healthy, 0.5=degraded, 0=unhealthy)
- `api_request_duration_seconds` - API latency by endpoint

### Prometheus UI

Access Prometheus UI at http://localhost:9090

Example queries:
```promql
# Request rate
rate(api_request_duration_seconds_count[5m])

# Average processing time
rate(job_processing_time_seconds_sum[5m]) / rate(job_processing_time_seconds_count[5m])

# Queue depth over time
job_queue_depth
```

## 🧪 Testing

### Run Tests

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Generate Prisma client
prisma generate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_jobs.py -v
```

### Test Coverage

Tests include:
- API endpoint tests (jobs, providers, health)
- Request/response validation
- Error handling
- Database operations
- Health checks

## 🛠️ Development

### Local Development Setup

1. **Install Python dependencies**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set up database**

```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Generate Prisma client
prisma generate

# Push schema to database
prisma db push
```

3. **Run API server**

```bash
python -m app.main
# Or with uvicorn
uvicorn app.main:app --reload
```

4. **Run Celery worker**

```bash
celery -A app.celery_app.celery_config worker --loglevel=info
```

### Code Quality

```bash
# Format code
black app tests

# Lint code
flake8 app tests

# Type checking
mypy app
```

## 🐳 Docker Commands

### Build and run all services

```bash
docker-compose up --build
```

### Run specific service

```bash
docker-compose up postgres redis
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Stop services

```bash
docker-compose down

# Remove volumes
docker-compose down -v
```

### Rebuild specific service

```bash
docker-compose up --build api
```

## 🔒 Security

### Environment Variables

Never commit sensitive values. Use `.env.example` as template.

Required secrets:
- `SECRET_KEY` - Application secret key
- `API_KEY` - API authentication key
- `DATABASE_URL` - PostgreSQL connection string

### API Authentication

In production, all `/api/` endpoints require `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/jobs
```

## 📝 Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- **Application**: `APP_NAME`, `APP_ENV`, `APP_DEBUG`, `LOG_LEVEL`
- **API**: `API_HOST`, `API_PORT`, `API_WORKERS`
- **Database**: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **Redis**: `REDIS_URL`, `REDIS_HOST`, `REDIS_PORT`
- **Celery**: `CELERY_BROKER_URL`, `CELERY_TASK_TIME_LIMIT`, etc.
- **Security**: `SECRET_KEY`, `API_KEY`
- **CORS**: `CORS_ORIGINS`

## 🚦 Health Checks

### Liveness Probe

Simple check that the service is running:

```bash
curl http://localhost:8000/health
# Response: {"status": "alive"}
```

### Readiness Probe

Comprehensive check of all dependencies:

```bash
curl http://localhost:8000/health/ready
```

Response includes:
- Overall status
- Database connection status and latency
- Redis connection status and latency

## 📦 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── routes/             # API route handlers
│   │   ├── models/             # Pydantic models
│   │   └── middleware/         # Request/error middleware
│   ├── celery_app/
│   │   ├── celery_config.py    # Celery configuration
│   │   ├── tasks.py            # Async tasks
│   │   └── worker.py           # Worker entry point
│   ├── db/
│   │   ├── prisma.py           # Database client
│   │   └── models.py           # Database operations
│   ├── monitoring/
│   │   ├── metrics.py          # Prometheus metrics
│   │   └── health.py           # Health check logic
│   └── utils/
│       ├── logger.py           # Structured logging
│       └── errors.py           # Custom exceptions
├── prisma/
│   └── schema.prisma           # Database schema
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image
├── .env.example               # Environment template
└── prometheus.yml             # Prometheus config
```

## 🎯 Next Steps (Phase 2+)

This Phase 1 foundation enables:

- ✅ AI provider integrations (OpenAI, Runway, Stability AI, etc.)
- ✅ Advanced retry and circuit breaker patterns
- ✅ Frontend application integration
- ✅ Advanced monitoring and alerting
- ✅ Auto-scaling based on queue depth
- ✅ S3/blob storage for video outputs
- ✅ Webhook notifications for job completion
- ✅ Rate limiting and quota management

## 📄 License

[Your License Here]

## 🤝 Contributing

[Contributing guidelines here]

## 📞 Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
