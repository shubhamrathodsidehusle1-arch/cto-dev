#!/bin/bash

set -e

echo "🚀 Setting up AI Video Generation Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please update with your configuration."
else
    echo "✅ .env already exists."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Generate Prisma client
echo "🔧 Generating Prisma client..."
prisma generate

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Start services: docker-compose up -d postgres redis"
echo "3. Push database schema: prisma db push"
echo "4. Run API: python -m app.main"
echo "5. Run Celery worker: celery -A app.celery_app.celery_config worker --loglevel=info"
