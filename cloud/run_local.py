"""
Simple local development server for Auto Finance Bot
Runs both frontend and backend without Docker
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ Backend dependencies found")
        return True
    except ImportError:
        print("❌ Backend dependencies missing")
        print("\nInstall them with:")
        print("  cd backend && pip install -r requirements.txt")
        return False

def check_env():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  No .env file found")
        if os.path.exists('env.template'):
            print("\nCreating .env from template...")
            with open('env.template', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print("✅ Created .env - Please edit it with your API keys!")
        return False
    return True

def start_backend():
    """Start FastAPI backend"""
    print("🚀 Starting backend on http://localhost:8000")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=os.getcwd()
    )
    return backend_process

def start_frontend():
    """Start simple HTTP server for frontend"""
    print("🎨 Starting frontend on http://localhost:3000")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000"],
        cwd=os.path.join(os.getcwd(), "frontend")
    )
    return frontend_process

def main():
    print("=" * 50)
    print("🤖 Auto Finance Bot - Local Development Server")
    print("=" * 50)
    print()
    
    # Check environment
    if not check_env():
        print("\n⚠️  Please configure .env file and try again")
        input("\nPress Enter to exit...")
        return
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return
    
    print()
    print("Starting services...")
    print("-" * 50)
    
    # Start backend
    backend = start_backend()
    time.sleep(2)  # Give backend time to start
    
    # Start frontend
    frontend = start_frontend()
    time.sleep(1)
    
    print()
    print("=" * 50)
    print("✅ Services running!")
    print("=" * 50)
    print()
    print("📍 Frontend: http://localhost:3000")
    print("📍 API: http://localhost:8000")
    print("📍 API Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop all services")
    print("=" * 50)
    print()
    
    # Open browser
    time.sleep(1)
    webbrowser.open('http://localhost:3000')
    
    try:
        # Wait for user to stop
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping services...")
        backend.terminate()
        frontend.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()

