#!/bin/bash

# Auto Finance Bot - Local Startup Script

echo "🚀 Starting Auto Finance Bot (Cloud Version)"
echo "==========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp env.template .env
    echo "✅ Created .env - Please edit it with your API keys!"
    echo ""
    exit 1
fi

# Check Docker
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Desktop."
    exit 1
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"

