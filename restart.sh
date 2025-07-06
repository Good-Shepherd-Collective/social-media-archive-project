#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Bot Restart Script ===${NC}"

# Change to script directory
cd "$(dirname "$0")"

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found!${NC}"
    exit 1
fi

# Check if required variables are set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}Error: TELEGRAM_BOT_TOKEN not found in .env!${NC}"
    exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
    echo -e "${RED}Error: WEBHOOK_URL not found in .env!${NC}"
    exit 1
fi

# Clear Python cache
echo -e "${YELLOW}Clearing Python cache...${NC}"
find . -path ./venv -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -path ./venv -prune -o -name "*.pyc" -type f -exec rm -f {} + 2>/dev/null || true
echo -e "${GREEN}✓ Cache cleared${NC}"

# Check for running bot processes
echo -e "${YELLOW}Checking for running bot processes...${NC}"
BOT_PIDS=$(pgrep -f "python.*main_bot.py" || true)

if [ -n "$BOT_PIDS" ]; then
    echo -e "${YELLOW}Stopping bot processes: $BOT_PIDS${NC}"
    kill $BOT_PIDS 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    BOT_PIDS=$(pgrep -f "python.*main_bot.py" || true)
    if [ -n "$BOT_PIDS" ]; then
        echo -e "${YELLOW}Force stopping bot processes...${NC}"
        kill -9 $BOT_PIDS 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Bot stopped${NC}"
else
    echo -e "${GREEN}✓ No bot processes running${NC}"
fi

# Ensure logs directory exists
mkdir -p logs

# Start the bot
echo -e "${YELLOW}Starting bot...${NC}"
nohup python main_bot.py > logs/bot_startup.log 2>&1 &
BOT_PID=$!
sleep 3

# Check if bot started successfully
if ps -p $BOT_PID > /dev/null; then
    echo -e "${GREEN}✓ Bot started with PID: $BOT_PID${NC}"
else
    echo -e "${RED}✗ Bot failed to start! Check logs/bot_startup.log${NC}"
    tail -20 logs/bot_startup.log
    exit 1
fi

# Verify webhook is set
echo -e "${YELLOW}Verifying webhook...${NC}"
WEBHOOK_CHECK=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo")

if echo "$WEBHOOK_CHECK" | grep -q "\"url\":\"${WEBHOOK_URL}\""; then
    echo -e "${GREEN}✓ Webhook is correctly set to: ${WEBHOOK_URL}${NC}"
else
    echo -e "${YELLOW}Setting webhook...${NC}"
    WEBHOOK_RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
        -d "url=${WEBHOOK_URL}")
    
    if echo "$WEBHOOK_RESULT" | grep -q "\"ok\":true"; then
        echo -e "${GREEN}✓ Webhook set successfully${NC}"
    else
        echo -e "${RED}✗ Failed to set webhook!${NC}"
        echo "$WEBHOOK_RESULT"
    fi
fi

# Show webhook status
echo -e "${YELLOW}Current webhook status:${NC}"
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool | grep -E "url|pending_update_count|last_error_message" || true

echo -e "${GREEN}=== Bot restart complete ===${NC}"
echo -e "${YELLOW}Logs:${NC}"
echo "  - Bot output: logs/bot_startup.log"
echo "  - Bot logs: logs/bot.log"
echo ""
echo -e "${YELLOW}Monitor bot:${NC}"
echo "  tail -f logs/bot.log"
