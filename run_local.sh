#!/bin/bash
# Script to run the Telegram bot locally with development configuration

echo "Starting Telegram bot in LOCAL development mode..."
echo "Using development bot: @gsc_local_data_bot"
echo "Make sure to update TELEGRAM_AUTHORIZED_USERS in .env.local with your Telegram user ID"
echo ""

# Set environment to use local config
export ENV_FILE=".env.local"

# Run the bot
cd "$(dirname "$0")"
source venv/bin/activate
python twitter/telegram_bot.py
