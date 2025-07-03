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