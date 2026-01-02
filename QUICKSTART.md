# Quick Start Guide

Get the AI Video Generation Backend up and running in minutes!

## 🎯 Prerequisites

- Docker and Docker Compose installed
- Port 8000, 5432, 6379, 9090 available

## 🚀 Start Everything

```bash
# 1. Start all services with Docker Compose
docker compose up --build

# Wait for services to be ready (about 30-60 seconds)
# You'll see: "✅ Setup complete! Starting application..."
```

## ✅ Verify Services

```bash
# Check API is running
curl http://localhost:8000/health
# Expected: {"status": "alive"}

# Check readiness
curl http://localhost:8000/health/ready

# View API documentation
open http://localhost:8000/docs
```

## 📝 Create Your First Job

```bash
# Create a video generation job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "demo-user",
    "prompt": "A beautiful sunset over the ocean",
    "metadata": {"priority": "high"},
    "maxRetries": 3
  }'

# Response will include job ID, e.g.:
# {"id": "clxxxxx...", "status": "queued", ...}
```

## 🔍 Check Job Status

```bash
# Replace {job_id} with the ID from above
curl http://localhost:8000/api/v1/jobs/{job_id}
```

Job will progress through states:
1. `queued` - Job created, waiting for worker
2. `processing` - Worker is generating video
3. `completed` - Success! Check `result` field
4. `failed` - Check `errorMessage` field

## 📊 Monitor System

- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Logs**: `docker compose logs -f api`
- **Worker Logs**: `docker compose logs -f celery_worker`

## 🛑 Stop Services

```bash
docker compose down

# Remove data volumes
docker compose down -v
```

## 🐛 Troubleshooting

### API won't start
```bash
# Check database is ready
docker compose logs postgres

# Check Redis is ready
docker compose logs redis

# View API logs
docker compose logs api
```

### Jobs not processing
```bash
# Check Celery worker
docker compose logs celery_worker

# Restart worker
docker compose restart celery_worker
```

### Reset everything
```bash
docker compose down -v
docker compose up --build
```

## 📚 Next Steps

- Read the [full README](README.md)
- Explore [API documentation](http://localhost:8000/docs)
- Check out the code in `/backend/app/`
- Review tests in `/backend/tests/`

## 🎓 Example Workflows

### List all jobs
```bash
curl http://localhost:8000/api/v1/jobs
```

### Filter by user
```bash
curl "http://localhost:8000/api/v1/jobs?userId=demo-user"
```

### Filter by status
```bash
curl "http://localhost:8000/api/v1/jobs?status=completed"
```

### Delete a job
```bash
curl -X DELETE http://localhost:8000/api/v1/jobs/{job_id}
```

### Check provider health
```bash
curl http://localhost:8000/api/v1/providers/status
```

### Test a provider
```bash
curl -X POST http://localhost:8000/api/v1/providers/test \
  -H "Content-Type: application/json" \
  -d '{"provider": "test_provider", "timeout": 30}'
```

Happy building! 🚀
