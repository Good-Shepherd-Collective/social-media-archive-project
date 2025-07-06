#!/bin/bash
# Quick health check for the social media bot

echo "Social Media Archive Bot Health Check"
echo "====================================="
echo ""

# Check systemd service status
echo "Service Status:"
sudo systemctl is-active social-media-bot && echo "✅ Service is ACTIVE" || echo "❌ Service is NOT ACTIVE"
echo ""

# Check process
echo "Process Info:"
if pgrep -f "main_bot.py" > /dev/null; then
    echo "✅ Bot process is running"
    ps aux | grep -E "python.*main_bot.py" | grep -v grep
else
    echo "❌ Bot process not found"
fi
echo ""

# Check recent logs
echo "Recent Activity (last 5 entries):"
tail -n 5 logs/bot.log | while read line; do
    echo "  $line"
done
echo ""

# Check webhook connectivity (if bot token is available)
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Telegram API Status:"
    if curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | grep -q '"ok":true'; then
        echo "✅ Bot is connected to Telegram"
    else
        echo "❌ Bot connection issue"
    fi
fi

echo ""
echo "To view full logs: sudo journalctl -u social-media-bot -f"
