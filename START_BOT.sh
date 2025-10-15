#!/bin/bash
echo "========================================="
echo " Auto Finance Telegram Bot Launcher"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo ""
    echo "Please create .env file with your API keys:"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo ""
    echo "Copy .env.example to .env and fill in your keys."
    echo ""
    exit 1
fi

echo "Starting bot GUI..."
echo ""
python3 bot_gui_new.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to start bot!"
    echo ""
    echo "Make sure you have installed all dependencies:"
    echo "  pip3 install -r requirements.txt"
    echo ""
fi

