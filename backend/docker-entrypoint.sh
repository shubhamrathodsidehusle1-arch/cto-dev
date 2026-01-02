#!/bin/bash
set -e

echo "🚀 Starting AI Video Generation Backend..."

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h "${DATABASE_URL%%@*}" > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Wait for Redis
echo "⏳ Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready"

# Generate Prisma client if not exists
if [ ! -d "node_modules/.prisma" ]; then
    echo "🔧 Generating Prisma client..."
    prisma generate
fi

# Run Prisma migrations or push schema
echo "🔧 Setting up database..."
prisma db push --skip-generate

echo "✅ Setup complete! Starting application..."

# Execute the main command
exec "$@"
