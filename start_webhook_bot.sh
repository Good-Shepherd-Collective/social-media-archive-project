#!/bin/bash
# Start the Telegram bot in webhook mode

cd /home/ubuntu/social-media-archive-project
source venv/bin/activate

echo "🚀 Starting Telegram bot in WEBHOOK mode..."
echo "Server: $(hostname -f)"
echo "Port: 8443"
echo "Webhook URL: https://ov-ab103a.infomaniak.ch/webhook"
echo ""

# Start the webhook bot
python twitter/webhook_bot.py
