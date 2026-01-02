.PHONY: help install generate-prisma db-push test lint format clean run-api run-worker docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make generate-prisma - Generate Prisma client"
	@echo "  make db-push        - Push Prisma schema to database"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Lint code with flake8"
	@echo "  make format         - Format code with black"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make run-api        - Run FastAPI server"
	@echo "  make run-worker     - Run Celery worker"
	@echo "  make docker-up      - Start Docker Compose services"
	@echo "  make docker-down    - Stop Docker Compose services"

install:
	pip install -r requirements.txt

generate-prisma:
	prisma generate

db-push:
	prisma db push

test:
	pytest -v

lint:
	flake8 app tests

format:
	black app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

run-api:
	python -m app.main

run-worker:
	celery -A app.celery_app.celery_config worker --loglevel=info

docker-up:
	cd .. && docker-compose up --build

docker-down:
	cd .. && docker-compose down
