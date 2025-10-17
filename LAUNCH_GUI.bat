@echo off
REM Auto Finance Bot Manager Launcher
REM Double-click this file to start the GUI

cd /d "%~dp0"

REM Check if .env exists
if not exist .env (
    echo.
    echo [!] No .env file found!
    echo.
    echo This appears to be your first time running the bot.
    echo The GUI will help you set up your API keys.
    echo.
    pause
)

REM Launch GUI (with visible console)
echo.
echo Launching Bot Manager GUI...
echo.
python bot_gui.py

REM If GUI closes, script ends
echo.
echo GUI closed.
pause

