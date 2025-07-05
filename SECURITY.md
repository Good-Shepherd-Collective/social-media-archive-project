# Security Notice

## API Key Security

**IMPORTANT**: Never commit API keys or sensitive credentials to the repository.

### Setting up API Keys Securely

1. **RapidAPI Key**:
   - Sign up at [RapidAPI](https://rapidapi.com/)
   - Subscribe to the required APIs:
     - [Instagram Scraper](https://rapidapi.com/social-api/api/instagram-scrapper-posts-reels-stories-downloader)
     - [Facebook Scraper](https://rapidapi.com/ytdlfree/api/facebook-scraper3)
     - [TikTok Downloader](https://rapidapi.com/yi005/api/tiktok-video-no-watermark2)
   - Copy your API key from the RapidAPI dashboard
   - Add it to your `.env` file (never commit this file)

2. **Telegram Bot Token**:
   - Create a bot with [@BotFather](https://t.me/botfather)
   - Copy the bot token
   - Add it to your `.env` file

3. **Database Credentials**:
   - Use strong passwords for your PostgreSQL database
   - Consider using environment-specific credentials
   - Never use default passwords in production

### Best Practices

1. **Use Environment Variables**: All sensitive data should be in `.env` files
2. **Git Ignore**: Ensure `.env` is in `.gitignore`
3. **Rotate Keys**: Regularly rotate API keys and passwords
4. **Limit Permissions**: Use the minimum required permissions for database users
5. **Monitor Usage**: Keep track of API usage to detect anomalies

### If You Accidentally Commit Credentials

1. **Immediately revoke** the exposed credentials
2. **Generate new** credentials
3. **Update** your `.env` file with new credentials
4. Consider using `git filter-branch` or BFG Repo-Cleaner to remove from history
5. **Force push** the cleaned history (coordinate with team members)

### Reporting Security Issues

If you discover a security vulnerability, please email [your-email@example.com] instead of using the issue tracker.
