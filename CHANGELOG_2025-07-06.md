# Social Media Archive Bot - Updates 2025-07-06

## Summary
Implemented comprehensive monitoring, auto-restart capabilities, and improved the archive viewer for the Social Media Archive Bot.

## Major Changes

### 1. Production Monitoring & Auto-Restart Setup
- Created systemd services for automatic startup and restart:
  - `social-media-bot.service` - Main Telegram bot service
  - `media-server.service` - HTTP server for serving archived content
  - `bot-monitor.service` - Monitoring service with email alerts

### 2. Email Alerts System
- Configured Gmail SMTP integration for monitoring alerts
- Alerts sent to: cody@goodshepherdcollective.org
- Notifications for:
  - Service failures
  - Automatic restart attempts
  - Service recovery

### 3. Enhanced Archive Viewer (`view_archive`)
- Added database summary statistics at the top:
  - Total post count
  - Posts by platform breakdown
  - Posts by user
  - Media file statistics
- Fixed Twitter URL format (tweet_ instead of twitter_)
- Added direct links to locally hosted content:
  - JSON data files
  - Media files (images, videos)
- Improved formatting and error handling

### 4. Monitoring Scripts Created
- `monitor_bot_email.py` - Main monitoring script with email alerts
- `check_bot_health.sh` - Quick health check script
- `setup_email_alerts.sh` - Email configuration helper
- `BOT_MONITORING.md` - Comprehensive monitoring documentation

## Files Added/Modified

### New Files:
- `/etc/systemd/system/social-media-bot.service`
- `/etc/systemd/system/media-server.service`
- `/etc/systemd/system/bot-monitor.service`
- `monitor_bot_email.py`
- `check_bot_health.sh`
- `setup_email_alerts.sh`
- `BOT_MONITORING.md`
- `.email_env` (email configuration)

### Modified Files:
- `view_archive` - Enhanced with summary stats and correct URLs

## Current Status
- ✅ Bot running 24/7 with auto-restart
- ✅ Media server serving files at https://ov-ab103a.infomaniak.ch/data/
- ✅ Email monitoring active
- ✅ 22 posts archived (Facebook: 10, TikTok: 6, Instagram: 4, Twitter: 2)
- ✅ 41 media files stored

## Access Points
- Telegram Bot: @[bot_name]
- Archive Browser: https://ov-ab103a.infomaniak.ch/data/
- Media Files: https://ov-ab103a.infomaniak.ch/data/media/

## Monitoring Commands
```bash
# Check all services
sudo systemctl status social-media-bot media-server bot-monitor

# View bot logs
sudo journalctl -u social-media-bot -f

# View monitor logs
tail -f logs/monitor.log

# Quick health check
./check_bot_health.sh

# View archive
./view_archive
```
