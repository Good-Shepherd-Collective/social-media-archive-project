#!/bin/bash
# Simple bot monitor that checks if the process is running

BOT_SCRIPT="main_bot.py"
LOG_FILE="/home/ubuntu/social-media-archive-project/logs/monitor.log"

# Function to check if bot is running
is_bot_running() {
    pgrep -f "$BOT_SCRIPT" > /dev/null
    return $?
}

# Function to start the bot
start_bot() {
    cd /home/ubuntu/social-media-archive-project
    nohup python3 $BOT_SCRIPT >> logs/bot.log 2>&1 &
    echo "$(date): Bot started with PID $!" >> "$LOG_FILE"
}

# Main check
if ! is_bot_running; then
    echo "$(date): Bot not running, attempting to restart..." >> "$LOG_FILE"
    start_bot
else
    echo "$(date): Bot is running" >> "$LOG_FILE"
fi
