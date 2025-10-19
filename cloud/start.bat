@echo off
REM Auto Finance Bot - Windows Startup Script

echo.
echo 🚀 Starting Auto Finance Bot (Cloud Version)
echo ===========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  No .env file found. Creating from template...
    copy env.template .env
    echo ✅ Created .env - Please edit it with your API keys!
    echo.
    pause
    exit
)

REM Check Docker
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please install Docker Desktop.
    pause
    exit
)

REM Start services
echo 🐳 Starting Docker containers...
docker-compose up -d

echo.
echo ✅ Services started!
echo.
echo 📍 Frontend: http://localhost:3000
echo 📍 API: http://localhost:8000
echo 📍 API Docs: http://localhost:8000/docs
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f
echo.
pause

