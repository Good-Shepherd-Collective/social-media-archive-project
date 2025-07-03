# Environment-Aware Storage Configuration

The Twitter scraper now supports environment-aware storage, allowing you to save scraped tweets to different locations based on your environment setup.

## Overview

The storage system uses environment variables to determine where to save scraped tweet data:

- **Local Environment**: Save only to local storage path
- **Server Environment**: Save only to server storage path  
- **Both Environments**: Save to both local and server paths (default)

## Environment Variables

Add these variables to your `.env` file:

```bash
# Storage Configuration
# Options: 'local', 'server', 'both' (default: 'both')
ENVIRONMENT=both

# Local storage path (relative to the script location)
LOCAL_STORAGE_PATH=../scraped_data

# Server storage path (absolute path)
SERVER_STORAGE_PATH=/home/ubuntu/social-media-archive-project/scraped_data
```

## Configuration Options

### ENVIRONMENT
- `local`: Save tweets only to the local storage path
- `server`: Save tweets only to the server storage path
- `both`: Save tweets to both locations (default behavior)

### LOCAL_STORAGE_PATH
- Path where tweets are saved in local environment
- Can be relative or absolute path
- Default: `../scraped_data`

### SERVER_STORAGE_PATH
- Path where tweets are saved in server environment
- Should be an absolute path
- Default: `/home/ubuntu/social-media-archive-project/scraped_data`

## Usage Examples

### 1. Development Environment (Local Only)
```bash
export ENVIRONMENT=local
# or modify .env file: ENVIRONMENT=local
```

### 2. Production Server (Server Only)
```bash
export ENVIRONMENT=server
# or modify .env file: ENVIRONMENT=server
```

### 3. Hybrid Setup (Both Local and Server)
```bash
export ENVIRONMENT=both
# or modify .env file: ENVIRONMENT=both
```

## Testing Configuration

Use the test script to verify your configuration:

```bash
cd twitter
python3 test_storage.py
```

This will show you:
- Current environment setting
- Storage paths being used
- Where a sample tweet would be saved

## Telegram Bot Features

The Telegram bot now includes additional commands to check storage configuration:

- `/storage` - View current storage configuration
- `/status` - Bot status including storage info
- When scraping tweets, the bot will show how many locations the tweet was saved to

## File Structure

After implementation, your project structure will look like:

```
social-media-archive-project/
├── twitter/
│   ├── storage_utils.py          # New storage management utility
│   ├── telegram_bot.py           # Updated main bot
│   ├── telegram_bot_simple.py    # Updated simple bot
│   ├── telegram_bot_handlers.py  # Updated handlers bot
│   ├── test_storage.py           # Storage configuration test
│   └── ...
├── scraped_data/                 # Server storage location
│   └── tweet_*.json
└── .env                          # Updated with storage variables
```

## Implementation Details

The storage system is implemented through:

1. **StorageManager Class** (`storage_utils.py`):
   - Manages storage paths based on environment
   - Handles saving to multiple locations
   - Provides configuration information

2. **Updated Bot Files**:
   - All telegram bot files now use the StorageManager
   - Tweet data includes environment information
   - Success messages show save locations

3. **Environment Integration**:
   - Reads configuration from environment variables
   - Supports runtime environment changes
   - Backwards compatible with existing setups

## Troubleshooting

### Permission Issues
Ensure the bot has write permissions to both storage directories:
```bash
mkdir -p /home/ubuntu/social-media-archive-project/scraped_data
chmod 755 /home/ubuntu/social-media-archive-project/scraped_data
```

### Path Issues
- Use absolute paths for server storage
- Ensure relative paths are correct relative to script location
- Test with `test_storage.py` before running the bot

### Environment Variable Issues
- Check `.env` file is in the project root
- Verify environment variables are loaded correctly
- Use `python3 -c "import os; print(os.getenv('ENVIRONMENT'))"` to test
