# Social Media Archive Project

A comprehensive project to scrape and archive content from multiple social media platforms.

## Project Structure

```
social-media-archive-project/
├── .env                    # Environment variables (credentials)
├── .env.example           # Environment variables template
├── requirements.txt       # Global dependencies
├── scraped_data/         # All scraped data stored here
├── twitter/              # Twitter/X scraping tools
│   ├── main.py           # Interactive Twitter scraper
│   ├── scrape_tweet.py   # Single tweet scraper
│   ├── requirements.txt  # Twitter-specific dependencies
│   └── README.md         # Twitter scraper documentation
├── facebook/             # Facebook scraping tools (planned)
├── instagram/            # Instagram scraping tools (planned)
└── tiktok/               # TikTok scraping tools (planned)
```

## Setup

1. **Clone and navigate to project:**
```bash
cd social-media-archive-project
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Platform-Specific Usage

### Twitter/X
```bash
cd twitter
pip install -r requirements.txt

# Interactive scraper
python main.py

# Single tweet scraper
python scrape_tweet.py https://x.com/username/status/123456789
```

### Facebook (Coming Soon)
```bash
cd facebook
# Tools coming soon
```

### Instagram (Coming Soon)
```bash
cd instagram
# Tools coming soon
```

### TikTok (Coming Soon)
```bash
cd tiktok
# Tools coming soon
```

## Data Storage

All scraped data is automatically saved to the `scraped_data/` folder with timestamped filenames for easy organization.

## Environment Variables

Required variables in `.env`:
- `TWITTER_USERNAME` - Your Twitter username
- `TWITTER_PASSWORD` - Your Twitter password
- `TWITTER_EMAIL` - Your Twitter email
- `TWITTER_EMAIL_PASSWORD` - Your email password
- `AUTH_TOKEN` - Twitter auth token from cookies
- `CT0` - Twitter CT0 token from cookies

## Security

- Never commit your `.env` file to version control
- Use the `.env.example` file as a template
- Keep your credentials secure and rotate them regularly
## Local Development Setup

### Running the Bot Locally

To avoid conflicts with the production bot running on the server, use the development bot:

1. **Update your local configuration**:
   ```bash
   # Edit .env.local and add your Telegram user ID
   TELEGRAM_AUTHORIZED_USERS=your_telegram_user_id_here
   ```

2. **Run the local development bot**:
   ```bash
   ./run_local.sh
   ```

3. **Test with the development bot**:
   - Message @gsc_local_data_bot on Telegram
   - Send `/start` to begin
   - Send tweet URLs to test scraping functionality

### Bot Tokens

- **Production Bot**: Used on the server (configured in `.env`)
- **Development Bot**: `@gsc_local_data_bot` (configured in `.env.local`)
  - Token: `7907408099:AAHlifWl_r87Uju6WFzAnx1RS7OIWiX8xt4`
  - Use this for local development and testing

This setup prevents the "Conflict: terminated by other getUpdates request" error when running the bot locally while the production bot is running on the server.

