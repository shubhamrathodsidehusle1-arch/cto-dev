# AI Video Generation Platform - Running Application

## 🚀 Application Status

The AI Video Generation Platform is now running successfully!

### Services Running

| Service | URL | Status |
|---------|-----|--------|
| **Frontend UI** | http://localhost:3000 | ✅ Running |
| **Backend API** | http://localhost:8000 | ✅ Running |
| **Database** | postgresql://localhost:5432 | ✅ Running |
| **Redis** | redis://localhost:6379 | ✅ Running |

## 🌐 Access the UI

### Primary Interface
Open your browser and navigate to:
```
http://localhost:3000
```

### Available Pages

1. **Home Page** - http://localhost:3000
   - Overview of the platform
   - Quick navigation to all features
   - Feature highlights

2. **Create Job** - http://localhost:3000/create
   - Create a new video generation job
   - Enter prompts and user ID
   - Set retry preferences

3. **View Jobs** - http://localhost:3000/jobs
   - List all video generation jobs
   - Real-time status updates
   - Job management interface

4. **Providers** - http://localhost:3000/providers
   - Monitor AI provider health
   - View response times and status
   - Test provider connectivity

## 🔌 API Endpoints

The backend API is available at http://localhost:8000 with the following endpoints:

### Health Check
- `GET /health` - Check API health status

### Jobs
- `GET /api/v1/jobs` - List all jobs
- `POST /api/v1/jobs` - Create a new job
- `GET /api/v1/jobs/{id}` - Get job details
- `DELETE /api/v1/jobs/{id}` - Delete a job

### Providers
- `GET /api/v1/providers/status` - Get provider health status
- `POST /api/v1/providers/test` - Test a specific provider

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## 📝 Quick Start

1. **Create a Job:**
   - Navigate to http://localhost:3000/create
   - Enter a User ID (e.g., "user-1")
   - Enter a prompt (e.g., "A futuristic city with flying cars at sunset")
   - Click "Generate Video"

2. **Monitor Progress:**
   - Navigate to http://localhost:3000/jobs
   - See your job in the list with real-time status
   - Status will update from "queued" → "processing" → "completed" or "failed"

3. **Check Providers:**
   - Navigate to http://localhost:3000/providers
   - View the health status of AI providers
   - Test provider connectivity

## 🛠 Development Notes

### Running Locally
- **Backend**: Running with `uvicorn` on port 8000
- **Frontend**: Running with Next.js dev server on port 3000
- **Database**: PostgreSQL 15 via Docker
- **Redis**: Redis 7 via Docker

### Logs
- **API Logs**: `tail -f backend/api.log`
- **Frontend Logs**: `tail -f frontend.log`

### Stop the Application
```bash
# Stop backend
pkill -f "uvicorn"

# Stop frontend
pkill -f "next dev"

# Stop Docker containers
docker compose down
```

## 📚 Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.12, Prisma ORM
- **Database**: PostgreSQL 15
- **Task Queue**: Celery with Redis
- **Monitoring**: Prometheus metrics

Enjoy creating videos with AI! 🎬
