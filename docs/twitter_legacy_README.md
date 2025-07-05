# Twitter Scraper

Twitter/X scraping module using the twscrape library.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file in the project root with Twitter credentials and cookies.

3. Run the scraper:
```bash
# Interactive scraper
python main.py

# Single tweet scraper
python scrape_tweet.py https://x.com/username/status/123456789
```

## Features

- Search tweets by keyword/query
- Scrape tweets from specific users
- Scrape individual tweets by URL
- Export to JSON or CSV format
- Automatic account setup with cookies

## Files

- `main.py` - Interactive scraper with menu options
- `scrape_tweet.py` - Single tweet scraper
- `requirements.txt` - Python dependencies