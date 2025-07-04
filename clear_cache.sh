#!/bin/bash

echo "🧹 Clearing Python cache..."
echo "============================"

# Stop any running bot processes
echo "🛑 Stopping bot processes..."
pkill -f webhook_bot || echo "   No webhook processes to stop"

# Clear Python cache
echo "🗑️ Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

echo "✅ Cache cleared successfully!"
echo ""
echo "🚀 Starting bot..."
nohup ./start_webhook_bot.sh > bot.log 2>&1 &
sleep 2
echo "✅ Bot started!"
echo ""
echo "📊 Status:"
ps aux | grep webhook_bot | grep -v grep | wc -l | xargs -I {} echo "   {} webhook process(es) running"
