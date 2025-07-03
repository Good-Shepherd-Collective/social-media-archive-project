#!/usr/bin/env python3
"""
Telegram Bot for Twitter Scraping
Receives tweet URLs via Telegram and automatically scrapes them
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from twscrape import API

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TwitterScraperBot:
    def __init__(self):
        self.api = API()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.authorized_users = os.getenv('TELEGRAM_AUTHORIZED_USERS', '').split(',')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    async def setup_twitter_account(self):
        """Setup Twitter account with cookies"""
        username = os.getenv('TWITTER_USERNAME')
        password = os.getenv('TWITTER_PASSWORD')
        email = os.getenv('TWITTER_EMAIL')
        email_password = os.getenv('TWITTER_EMAIL_PASSWORD')
        auth_token = os.getenv('AUTH_TOKEN')
        ct0 = os.getenv('CT0')
        
        if not all([username, password, email, email_password, auth_token, ct0]):
            logger.error("Missing Twitter credentials in environment variables")
            return False
        
        cookies = f"auth_token={auth_token}; ct0={ct0}"
        
        try:
            # Check if account exists and is active
            accounts = await self.api.pool.accounts_info()
            for acc in accounts:
                if acc['username'] == username and acc['active']:
                    logger.info(f"Twitter account {username} is already active")
                    return True
            
            # Add account with cookies
            await self.api.pool.add_account(
                username, password, email, email_password, cookies=cookies
            )
            logger.info(f"Twitter account {username} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Twitter account: {e}")
            return False
    
    async def scrape_tweet(self, url: str) -> dict:
        """Scrape a single tweet by URL"""
        try:
            # Extract tweet ID from URL
            tweet_id = int(url.split('/')[-1].split('?')[0])
            
            # Scrape tweet
            tweet = await self.api.tweet_details(tweet_id)
            
            if tweet:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'author': tweet.user.username,
                    'author_name': tweet.user.displayname,
                    'author_followers': tweet.user.followersCount,
                    'author_verified': tweet.user.verified,
                    'created_at': str(tweet.date),
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'reply_count': tweet.replyCount,
                    'quote_count': tweet.quoteCount,
                    'view_count': getattr(tweet, 'viewCount', None),
                    'url': url,
                    'scraped_at': str(datetime.now()),
                    'scraped_via': 'telegram_bot'
                }
                
                # Save to file
                filename = f"../scraped_data/tweet_{tweet_id}.json"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(tweet_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Tweet {tweet_id} scraped and saved to {filename}")
                return tweet_data
            else:
                logger.warning(f"Tweet not found or not accessible: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping tweet {url}: {e}")
            return None
    
    def is_authorized(self, user_id: str) -> bool:
        """Check if user is authorized to use the bot"""
        if not self.authorized_users or self.authorized_users == ['']:
            return True  # If no restrictions set, allow all users
        return str(user_id) in self.authorized_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        await update.message.reply_text(
            "🐦 **Twitter Scraper Bot**\\n\\n"
            "Send me a Twitter/X URL and I'll scrape it for you\\!\\n\\n"
            "**Commands:**\\n"
            "/start \\- Show this help message\\n"
            "/status \\- Check bot status\\n\\n"
            "**Usage:**\\n"
            "Just send a tweet URL like:\\n"
            "`https://x.com/username/status/123456789`",
            parse_mode='MarkdownV2'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        try:
            accounts = await self.api.pool.accounts_info()
            active_accounts = [acc for acc in accounts if acc['active']]
            
            status_msg = f"🤖 **Bot Status**\\n\\n"
            status_msg += f"✅ Bot is running\\n"
            status_msg += f"🐦 Active Twitter accounts: {len(active_accounts)}\\n"
            
            if active_accounts:
                for acc in active_accounts:
                    status_msg += f"  • @{acc['username']}\\n"
            
            await update.message.reply_text(status_msg, parse_mode='MarkdownV2')
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            await update.message.reply_text("❌ Error checking bot status")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages (tweet URLs)"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        message_text = update.message.text
        
        # Check if message contains a Twitter/X URL
        if not any(domain in message_text for domain in ['twitter.com', 'x.com']):
            await update.message.reply_text(
                "❌ Please send a valid Twitter/X URL\\n"
                "Example: `https://x.com/username/status/123456789`",
                parse_mode='MarkdownV2'
            )
            return
        
        # Extract URL from message
        words = message_text.split()
        tweet_url = None
        
        for word in words:
            if 'twitter.com' in word or 'x.com' in word:
                tweet_url = word
                break
        
        if not tweet_url:
            await update.message.reply_text("❌ Could not find a valid tweet URL in your message")
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Scraping tweet...")
        
        try:
            # Scrape the tweet
            tweet_data = await self.scrape_tweet(tweet_url)
            
            if tweet_data:
                # Send success message with tweet details
                success_msg = (
                    f"✅ **Tweet scraped successfully\\!**\\n\\n"
                    f"👤 **Author:** @{tweet_data['author']} \\({tweet_data['author_name']}\\)\\n"
                    f"📅 **Date:** {tweet_data['created_at']}\\n"
                    f"👍 **Likes:** {tweet_data['like_count']}\\n"
                    f"🔄 **Retweets:** {tweet_data['retweet_count']}\\n"
                    f"💬 **Replies:** {tweet_data['reply_count']}\\n\\n"
                    f"**Text:**\\n{tweet_data['text'][:200]}{'\\.\\.\\.' if len(tweet_data['text']) > 200 else ''}\\n\\n"
                    f"💾 Saved to: `tweet_{tweet_data['id']}\\.json`"
                )
                
                await processing_msg.edit_text(success_msg, parse_mode='MarkdownV2')
            else:
                await processing_msg.edit_text("❌ Failed to scrape tweet. It may be private or deleted.")
                
        except Exception as e:
            logger.error(f"Error processing tweet URL {tweet_url}: {e}")
            await processing_msg.edit_text("❌ Error occurred while scraping tweet")
    
    async def run_bot(self):
        """Run the Telegram bot"""
        # Setup Twitter account
        if not await self.setup_twitter_account():
            logger.error("Failed to setup Twitter account. Bot cannot start.")
            return
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start bot
        logger.info("Starting Telegram bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Keep the bot running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await application.stop()
            await application.shutdown()

async def main():
    """Main function"""
    try:
        bot = TwitterScraperBot()
        await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())