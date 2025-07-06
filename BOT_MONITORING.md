# Bot Monitoring and Auto-Restart Guide

This guide provides several methods to ensure your bot stays running and automatically restarts if it crashes.

## Method 1: Systemd Service (Recommended for Linux)

This is the most robust solution for Ubuntu/Linux systems.

### Setup:
```bash
# Run the setup script
./setup_systemd_service.sh
```

### Benefits:
- Automatic restart on crash
- Starts on system boot
- Integrated logging
- Resource limits
- Easy management

### Commands:
```bash
# Check status
sudo systemctl status social-media-bot

# View logs
sudo journalctl -u social-media-bot -f

# Stop bot
sudo systemctl stop social-media-bot

# Start bot
sudo systemctl start social-media-bot

# Restart bot
sudo systemctl restart social-media-bot

# Disable auto-start
sudo systemctl disable social-media-bot
```

## Method 2: Process Monitor with Alerts

Use the `monitor_bot.py` script for advanced monitoring with alerts.

### Setup:
1. Configure your admin Telegram chat ID:
```bash
export ADMIN_TELEGRAM_CHAT_ID="your-chat-id"
```

2. Run the monitor:
```bash
python3 monitor_bot.py &
```

3. (Optional) Add to systemd for the monitor itself:
```bash
# Create a service file for the monitor
sudo cp monitor_bot.py /usr/local/bin/
# Then create a systemd service for it
```

### Features:
- Checks if service is running
- Verifies bot is responding to Telegram API
- Sends Telegram alerts on issues
- Automatic restart attempts
- Optional email alerts

## Method 3: Docker with Auto-Restart

If you prefer containerization:

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down
```

### Benefits:
- Isolation
- Easy deployment
- Built-in health checks
- Automatic restarts

## Method 4: Simple Cron Monitor

For a basic solution:

1. Add to crontab:
```bash
crontab -e
```

2. Add this line to check every 5 minutes:
```
*/5 * * * * /home/ubuntu/social-media-archive-project/simple_monitor.sh
```

## Logging

All methods create logs in the `logs/` directory:
- `bot.log` - Main bot output
- `bot-error.log` - Error messages
- `monitor.log` - Monitor script logs

## Best Practices

1. **Use systemd** for production - it's the most reliable
2. **Set up alerts** so you know when issues occur
3. **Monitor logs** regularly for errors
4. **Test recovery** - manually stop the bot to ensure it restarts
5. **Set resource limits** to prevent memory/CPU issues

## Troubleshooting

### Bot keeps crashing:
1. Check logs for errors:
```bash
tail -n 100 logs/bot-error.log
sudo journalctl -u social-media-bot -n 100
```

2. Common issues:
- Missing environment variables
- Network connectivity
- API rate limits
- Memory issues

### Monitor not working:
1. Ensure proper permissions
2. Check if systemd service is enabled
3. Verify cron job is running: `crontab -l`

## Getting Your Telegram Chat ID

To receive alerts on Telegram:

1. Message your bot with `/start`
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response
4. Set it as environment variable: `export ADMIN_TELEGRAM_CHAT_ID="your-id"`
