@echo off
echo =========================================
echo  Auto Finance Telegram Bot Launcher
echo =========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file with your API keys:
    echo   - ANTHROPIC_API_KEY
    echo   - TELEGRAM_BOT_TOKEN
    echo.
    echo Copy .env.example to .env and fill in your keys.
    echo.
    pause
    exit /b 1
)

echo Starting bot GUI...
echo.
python bot_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start bot!
    echo.
    echo Make sure you have installed all dependencies:
    echo   pip install -r requirements.txt
    echo.
    pause
)

