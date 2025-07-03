#!/usr/bin/env python3
"""
Webhook-enabled Telegram Bot for Twitter Scraping
Production version that uses webhooks instead of polling
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from twscrape import API
from storage_utils import storage_manager

# Load environment variables
env_file = os.getenv("ENV_FILE", ".env")
load_dotenv(env_file)
print(f"Loading environment from: {env_file}")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WebhookTwitterBot:
    def __init__(self):
        self.api = API()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.authorized_users = os.getenv('TELEGRAM_AUTHORIZED_USERS', '').split(',')
        self.webhook_url = os.getenv('WEBHOOK_URL', '')
        self.webhook_port = int(os.getenv('WEBHOOK_PORT', '8443'))
        self.webhook_path = os.getenv('WEBHOOK_PATH', '/webhook')
        self.environment = os.getenv('BOT_ENVIRONMENT', 'development')
        self.server_name = os.getenv("SERVER_NAME", "Unknown")
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Initialize application
        self.application = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        mode = "🌐 WEBHOOK" if self.environment == 'production' else "🔍 POLLING"
        welcome_message = f"""
🤖 **Twitter Scraper Bot** ({mode})

Welcome! Send me Twitter/X URLs and I'll scrape them for you.

**Commands:**
/start - Show this message
/help - Show help information
/status - Check bot status

**Environment:** {self.environment}
**Server:** {os.getenv('SERVER_NAME', 'Unknown')}

Just send me a tweet URL to get started!
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🔗 **How to use:**

1. Find a tweet on Twitter/X
2. Copy the URL (e.g., https://twitter.com/user/status/123456)
3. Send it to me
4. I'll scrape the content and save it

**Supported formats:**
- twitter.com/user/status/id
- x.com/user/status/id
- Mobile links (m.twitter.com)
- Shortened URLs (t.co)

**What I save:**
- Tweet text and metadata
- Images and videos
- Thread conversations
- User information
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        status_text = f"""
📊 **Bot Status**

**Environment:** {self.environment}
**Mode:** {'Webhook' if self.environment == 'production' else 'Polling'}
**Server:** {os.getenv('SERVER_NAME', 'Unknown')}
**Storage:** {storage_manager.get_storage_info()}

**Twitter API:** {'✅ Connected' if self.api else '❌ Not connected'}
**Authorized Users:** {len(self.authorized_users)}
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = str(update.effective_user.id)
        
        if user_id not in self.authorized_users:
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        message_text = update.message.text
        
        # Check if message contains a Twitter URL
        if not any(domain in message_text.lower() for domain in ['twitter.com', 'x.com', 't.co']):
            await update.message.reply_text(
                "🔗 Please send me a Twitter/X URL to scrape.\n\n"
                "Example: https://twitter.com/user/status/123456"
            )
            return
        
        # Process the tweet URL
        await self.process_tweet_url(update, message_text)
    
    async def process_tweet_url(self, update: Update, url: str):
        """Process a tweet URL and scrape it"""
        try:
            # Send processing message
            processing_msg = await update.message.reply_text("🔄 Processing tweet...")
            
            # Import and use the scraping logic
            from scrape_tweet import scrape_tweet_by_url
            
            # Scrape the tweet
            tweet_data = await scrape_tweet_by_url(url)
            
            if tweet_data:
                # Check file locations and create response
                file_locations = []
                expected_filename = f"tweet_{tweet_data.get('id')}.json"
                
                # Check multiple possible locations
                possible_paths = [
                    f"./{expected_filename}",
                    f"./scraped_data/{expected_filename}",
                    f"/home/ubuntu/social-media-archive-project/{expected_filename}",
                    f"/home/ubuntu/social-media-archive-project/scraped_data/{expected_filename}"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        file_locations.append(path)
                
                # Create file URLs (remove duplicates)
                file_urls = []
                seen_filenames = set()
                for location in file_locations:
                    # Convert local path to web URL
                    filename = os.path.basename(location)
                    if filename not in seen_filenames:
                        file_url = f"https://ov-ab103a.infomaniak.ch/data/{filename}"
                        file_urls.append(file_url)
                        seen_filenames.add(filename)
                        logger.info(f"   Generated URL: {file_url}")
                
                # Prepare response in the requested format
                tweet_text = tweet_data.get('text', 'No text')
                if len(tweet_text) > 100:
                    display_text = tweet_text[:100] + "..."
                else:
                    display_text = tweet_text
                
                response_parts = [
                    "✅ Tweet scraped successfully!",
                    "",
                    f"👤 Author: @{tweet_data.get('author', 'Unknown')} ({tweet_data.get('author_name', 'Unknown')})",
                    f"📅 Date: {tweet_data.get('created_at', 'Unknown')}",
                    f"👍 Likes: {tweet_data.get('like_count', 0)} | 🔄 Retweets: {tweet_data.get('retweet_count', 0)} | 💬 Replies: {tweet_data.get('reply_count', 0)}",
                    "",
                    f"Text: {display_text}",
                    "",
                ]
                
                # Add file information
                if file_urls:
                    if len(file_urls) == 1:
                        response_parts.append(f"💾 Saved to: {file_urls[0]}")
                    else:
                        response_parts.append(f"💾 Saved to {len(file_urls)} location(s):")
                        for url in file_urls:
                            response_parts.append(f"  • {url}")
                else:
                    response_parts.append(f"💾 Saved locally (check server for file)")
                
                response_text = "\n".join(response_parts)
                
                # Edit the processing message
                await processing_msg.edit_text(response_text, parse_mode='Markdown')
                
                # Log the activity
                logger.info(f"Tweet scraped successfully by user {update.effective_user.id}: {tweet_data.get('id')}")
                
            else:
                await processing_msg.edit_text("❌ Failed to scrape tweet. The tweet may be private, deleted, or the URL is invalid.")
                logger.error(f"Tweet scraping failed for URL: {url}")
                
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            await processing_msg.edit_text(f"❌ Error processing tweet: {str(e)}")
    
    async def webhook_handler(self, request):
        """Handle incoming webhook requests"""
        try:
            # Get the JSON data from the request
            data = await request.json()
            
            # Create Update object
            update = Update.de_json(data, self.application.bot)
            
            # Process the update
            await self.application.process_update(update)
            
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(text="Error", status=500)
    
    async def setup_webhook(self):
        """Setup webhook with Telegram"""
        try:
            webhook_url = f"{self.webhook_url}{self.webhook_path}"
            
            # Set webhook
            await self.application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            
            logger.info(f"Webhook set to: {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def run_webhook(self):
        """Run bot in webhook mode"""
        logger.info("Starting bot in WEBHOOK mode")
        
        # Initialize the application
        await self.application.initialize()
        
        # Setup webhook
        if not await self.setup_webhook():
            logger.error("Failed to setup webhook")
            return
        
        # Create web application
        app = web.Application()
        app.router.add_post(self.webhook_path, self.webhook_handler)
        app.router.add_get("/data/{filename}", self.serve_json_file)
        
        # Start the web server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.webhook_port)
        await site.start()
        
        logger.info(f"Webhook server started on port {self.webhook_port}")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.application.stop()
            await runner.cleanup()
    
    async def run_polling(self):
        """Run bot in polling mode (development)"""
        logger.info("Starting bot in POLLING mode (development)")
        
        # Remove webhook if exists
        await self.application.bot.delete_webhook()
        
        # Start polling
        await self.application.run_polling(
            allowed_updates=["message", "callback_query"],
            poll_interval=2.0,
            timeout=10
        )
    
    async def run(self):
        """Run the bot based on environment"""
        if self.environment == 'production' and self.webhook_url:
            await self.run_webhook()
        else:
            await self.run_polling()

    
    async def serve_json_file(self, request):
        """Serve JSON files from the data directory"""
        try:
            filename = request.match_info['filename']
            
            # Security: only allow .json files and prevent directory traversal
            if not filename.endswith('.json') or '..' in filename or '/' in filename:
                return web.Response(text="Invalid filename", status=400)
            
            # Look for the file in multiple locations
            possible_paths = [
                f"./scraped_data/{filename}",
                f"/home/ubuntu/social-media-archive-project/scraped_data/{filename}",
                f"./{filename}",
                f"/home/ubuntu/social-media-archive-project/{filename}"
            ]
            
            for file_path in possible_paths:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    
                    return web.Response(
                        text=data,
                        content_type='application/json',
                        headers={'Content-Disposition': f'inline; filename="{filename}"'}
                    )
            
            return web.Response(text="File not found", status=404)
            
        except Exception as e:
            logger.error(f"Error serving file: {e}")
            return web.Response(text="Internal server error", status=500)

async def main():
    """Main function"""
    try:
        bot = WebhookTwitterBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
