# Telegram Bot Setup Guide

## 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Send `/newbot` command
4. Choose a name for your bot (e.g., "Twitter Scraper Bot")
5. Choose a username for your bot (must end with "bot", e.g., "twitter_scraper_bot")
6. Copy the bot token that BotFather provides

## 2. Get Your User ID (Optional - for security)

1. Search for `@userinfobot` on Telegram
2. Start a chat and it will tell you your user ID
3. Add this ID to the `TELEGRAM_AUTHORIZED_USERS` in your `.env` file

## 3. Configure Environment Variables

Add these to your `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_AUTHORIZED_USERS=your_user_id_here
```

## 4. Install Dependencies

```bash
cd twitter
pip install -r requirements.txt
```

## 5. Run the Bot

```bash
python telegram_bot.py
```

## 6. Using the Bot

1. Start a chat with your bot on Telegram
2. Send `/start` to see the welcome message
3. Send any tweet URL like: `https://x.com/username/status/123456789`
4. The bot will automatically scrape the tweet and save it to `scraped_data/`

## Bot Commands

- `/start` - Show help message
- `/status` - Check bot and Twitter account status
- Send any tweet URL to scrape it automatically

## Security Features

- Optional user authorization (only specified users can use the bot)
- Automatic Twitter account setup
- Error handling and logging
- Secure credential management