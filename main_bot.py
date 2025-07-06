"""
Good Shepherd Collective's Archive Bot
Enhanced to support Twitter, Instagram, Facebook, TikTok, and future platforms
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
import sys
from pathlib import Path

# Add parent directory to path for platform manager
sys.path.append('..')

from bot.platform_manager import PlatformManager
from bot.url_detector import URLDetector
from core.database_storage import database_storage
from core.data_models import UserContext

# Load environment variables
load_dotenv()

# Set up logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/bot.log')
    ]
)
logger = logging.getLogger(__name__)

class MultiPlatformBot:
    def __init__(self):
        # Initialize Telegram bot
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.application = Application.builder().token(bot_token).build()
        
        # Initialize platform manager and URL detector
        self.platform_manager = PlatformManager()
        self.url_detector = URLDetector()
        
        # Initialize Twitter API for traditional tweets
        self.twscrape_api = API()
        
        # Setup handlers
        self._setup_handlers()
        
        # Webhook configuration
        self.webhook_url = os.getenv('WEBHOOK_URL', 'https://ov-ab103a.infomaniak.ch/webhook')
        self.webhook_port = int(os.getenv('WEBHOOK_PORT', 8443))
        
        logger.info("Multi-platform bot initialized")

    def _setup_handlers(self):
        """Set up Telegram command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("platforms", self.platforms_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **Good Shepherd Collective's Archive Bot**

Welcome! I can archive content from multiple social media platforms.

**Supported Platforms:**
🐦 Twitter/X
📸 Instagram
📘 Facebook
🎵 TikTok

**How to use:**
Send me a social media URL along with:
• **Description** to add context (optional but encouraged!)
• **Hashtags** to categorize the content (e.g., #protest #climate)

**Example:**
```
https://twitter.com/user/status/123...
This shows the youth climate march in downtown today
#climateaction #protest
```

**Commands:**
/help - Show detailed help
/platforms - List supported platforms

Ready to archive! 📚
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📚 **Good Shepherd Collective's Archive Bot Help**

**How to use:**
Send a social media URL with optional description and hashtags:
```
URL
Your description here
#hashtag1 #hashtag2
```

**Supported URL formats:**

🐦 **Twitter/X:**
• https://twitter.com/user/status/123...
• https://x.com/user/status/123...

📸 **Instagram:**
• https://instagram.com/p/ABC123/
• https://instagram.com/reel/ABC123/

📘 **Facebook:**
• https://facebook.com/user/posts/123...
• https://fb.watch/abc123/

🎵 **TikTok:**
• https://tiktok.com/@user/video/123...

**Features:**
✅ Full content archival
✅ Media download
✅ Metadata extraction
✅ User attribution
✅ Custom descriptions
✅ Hashtag categorization
✅ Hashtag extraction

**Usage:**
1. Send me a supported URL
2. Add hashtags if desired (e.g., #settlers #killing)
3. I'll archive the content and provide download links

**Storage:**
• JSON data: Structured metadata
• Media files: Original quality when possible
• Web access: View archived content online

Need more help? Contact the administrator.
"""
        await update.message.reply_text(help_message, parse_mode='Markdown')

    def parse_user_message(self, text: str):
        """Parse user message to extract URLs, hashtags, and description
        
        Expected format:
        URL
        Description (optional)
        #hashtags (optional)
        
        Returns:
            tuple: (urls, hashtags, description)
        """
        import re
        
        # Extract all URLs first
        urls = self.url_detector.extract_urls(text)
        
        # Remove URLs from text for further processing
        text_without_urls = text
        for url in urls:
            text_without_urls = text_without_urls.replace(url, '')
        
        # Extract all hashtags from the remaining text
        hashtag_pattern = r'#(\w+)'
        found_hashtags = re.findall(hashtag_pattern, text_without_urls)
        hashtags = [f'#{tag}' for tag in found_hashtags]
        
        # Remove hashtags from text to get pure description
        text_without_hashtags = re.sub(hashtag_pattern, '', text_without_urls)
        
        # Clean up the description
        description = ' '.join(text_without_hashtags.split()).strip()
        
        return urls, hashtags, description

    async def platforms_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /platforms command"""
        platforms = self.platform_manager.get_supported_platforms()
        platform_list = "\n".join([f"• {platform.value.title()}" for platform in platforms])
        
        message = f"""
🌐 **Supported Platforms**

{platform_list}

**Status:** All platforms active and ready for archival!

Send me a URL from any supported platform to get started.
"""
        await update.message.reply_text(message, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with URLs"""
        try:
            message_text = update.message.text
            chat_id = update.message.chat_id
            user_id = update.message.from_user.id
            username = update.message.from_user.username or f"user_{user_id}"
            
            logger.info(f"Processing message from {username} (ID: {user_id})")
            logger.info(f"Message: {message_text}")
            
            # Parse message to extract URLs, hashtags, and description
            urls, hashtags, description = self.parse_user_message(message_text)
            
            if not urls:
                await update.message.reply_text(
                    "🔗 Please send me a social media URL to archive!\n\n"
                    "**Format:**\n"
                    "```\n"
                    "URL\n"
                    "Description (optional)\n"
                    "#hashtags (optional)\n"
                    "```\n\n"
                    "Use /help for more information.",
                    parse_mode='Markdown'
                )
                return

            # Process each URL
            for url in urls:
                await self._process_url(update, url, hashtags, description, user_id, username)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "❌ Sorry, an error occurred while processing your message. Please try again."
            )

    async def _process_url(self, update: Update, url: str, user_hashtags: list, description: str, user_id: int, username: str):
        """Process a single URL"""
        try:
            # Detect platform
            platform = self.url_detector.detect_platform(url)
            
            if not platform:
                await update.message.reply_text(f"❌ Unsupported URL: {url}")
                return

            # Create user context
            user_context = UserContext(
                telegram_user_id=user_id,
                telegram_username=username,
                notes=description
            )

            # Send processing message
            processing_msg = await update.message.reply_text(
                f"⏳ Processing {platform.value.title()} content...\n\n"
                f"🔗 URL: {url}\n"
                f"📊 Platform: {platform.value.title()}\n"
                f"👤 User: @{username}"
            )

            logger.info(f"   🎯 Platform detected: {platform}")
            logger.info(f"   🔗 URL: {url}")
            logger.info(f"   #️⃣ Hashtags: {user_hashtags}")
            logger.info(f"   🚀 Starting {platform} scraping...")

            # Scrape content using platform manager
            try:
                post_data = await self.platform_manager.scrape_url(url, user_context)
                
                if not post_data:
                    await self._send_error_response(update, platform, "No data retrieved", processing_msg)
                    return

                
                # Save post data to JSON file
                json_result = self.save_post_to_json(post_data, platform, user_context, user_hashtags)

                # Send success response with detailed format
                await self._send_success_response(update, platform, post_data, user_hashtags, processing_msg, json_result)

            except Exception as scraping_error:
                logger.error(f"Scraping error: {scraping_error}")
                await self._send_error_response(update, platform, str(scraping_error), processing_msg)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await update.message.reply_text(f"❌ Error processing {url}: {str(e)}")

    
    def save_post_to_json(self, post_data, platform, user_context=None, user_hashtags=None):
        """Save SocialMediaPost to JSON file with user attribution and media downloads"""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("/home/ubuntu/social-media-archive-project/media_storage/data")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create media directory for downloads
            media_dir = Path("/home/ubuntu/social-media-archive-project/media_storage/data/media")
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # Download media files and update media objects
            downloaded_media = []
            if post_data.media:
                import httpx
                for i, media in enumerate(post_data.media):
                    try:
                        # Create filename for local storage
                        # Extract file extension properly
                        if media.media_type.value == 'video':
                            file_extension = 'mp4'
                        elif media.media_type.value == 'photo':
                            file_extension = 'jpg'
                        elif media.media_type.value == 'animated_gif':
                            file_extension = 'gif'
                        else:
                            # Try to extract from URL
                            import re
                            ext_match = re.search(r'\.([a-zA-Z0-9]{2,4})(?:\?|$)', media.url)
                            file_extension = ext_match.group(1) if ext_match else 'mp4'
                        local_filename = f"{post_data.id}_media_{i}.{file_extension}"
                        local_path = media_dir / local_filename
                        
                        # Download the media file
                        with httpx.Client() as client:
                            response = client.get(media.url, timeout=30)
                            if response.status_code == 200:
                                with open(local_path, 'wb') as f:
                                    f.write(response.content)
                                
                                downloaded_media.append({
                                    'url': media.url,
                                    'type': media.media_type.value if hasattr(media.media_type, 'value') else str(media.media_type),
                                    'width': media.width,
                                    'height': media.height,
                                    'mime_type': media.mime_type,
                                    'local_path': str(local_path),
                                    'hosted_url': f"https://ov-ab103a.infomaniak.ch/data/media/{local_filename}",
                                    'file_size': local_path.stat().st_size if local_path.exists() else None
                                })
                                logger.info(f"Downloaded media file: {local_filename}")
                                # Check if this is a Facebook video that needs audio merging
                                if (post_data.platform.value == 'facebook' and 
                                    media.media_type.value == 'video' and
                                    hasattr(post_data, 'raw_data') and 
                                    post_data.raw_data.get('_audio_stream')):
                                    
                                    # Download and merge audio
                                    audio_url = post_data.raw_data['_audio_stream'].get('base_url')
                                    if audio_url:
                                        logger.info(f"Downloading audio stream for Facebook video...")
                                        audio_path = local_path.parent / f"{post_data.id}_audio.mp4"
                                        merged_path = local_path.parent / f"{post_data.id}_merged.mp4"
                                        
                                        try:
                                            # Download audio
                                            audio_response = client.get(audio_url, timeout=30)
                                            if audio_response.status_code == 200:
                                                with open(audio_path, 'wb') as f:
                                                    f.write(audio_response.content)
                                                
                                                # Merge with ffmpeg
                                                import subprocess
                                                cmd = [
                                                    'ffmpeg', '-i', str(local_path), '-i', str(audio_path),
                                                    '-c:v', 'copy', '-c:a', 'copy', '-y', str(merged_path)
                                                ]
                                                result = subprocess.run(cmd, capture_output=True, text=True)
                                                
                                                if result.returncode == 0:
                                                    # Replace original with merged
                                                    import shutil
                                                    shutil.move(str(merged_path), str(local_path))
                                                    logger.info(f"Successfully merged video with audio")
                                                    downloaded_media[-1]['merged'] = True
                                                else:
                                                    logger.error(f"Failed to merge: {result.stderr}")
                                                
                                                # Clean up
                                                if audio_path.exists():
                                                    audio_path.unlink()
                                                if merged_path.exists():
                                                    merged_path.unlink()
                                                    
                                        except Exception as merge_error:
                                            logger.error(f"Failed to merge audio: {merge_error}")
                                
                            else:
                                # Keep original if download fails
                                downloaded_media.append({
                                    'url': media.url,
                                    'type': media.media_type.value if hasattr(media.media_type, 'value') else str(media.media_type),
                                    'width': media.width,
                                    'height': media.height,
                                    'mime_type': media.mime_type,
                                    'local_path': None,
                                    'hosted_url': None,
                                    'download_error': f"HTTP {response.status_code}"
                                })
                    except Exception as media_error:
                        logger.error(f"Failed to download media {i}: {media_error}")
                        downloaded_media.append({
                            'url': media.url,
                            'type': media.media_type.value if hasattr(media.media_type, 'value') else str(media.media_type),
                            'width': media.width,
                            'height': media.height,
                            'mime_type': media.mime_type,
                            'local_path': None,
                            'hosted_url': None,
                            'download_error': str(media_error)
                        })
            
            # Convert SocialMediaPost to dictionary with enhanced data
            post_dict = {
                'id': post_data.id,
                'platform': post_data.platform.value if hasattr(post_data.platform, 'value') else str(post_data.platform),
                'url': post_data.url,
                'text': post_data.text,
                'author': {
                    'username': post_data.author.username if post_data.author else None,
                    'display_name': post_data.author.display_name if post_data.author else None,
                    'followers_count': post_data.author.followers_count if post_data.author else 0,
                    'verified': post_data.author.verified if post_data.author else False,
                    'profile_url': post_data.author.profile_url if post_data.author else None,
                    'avatar_url': post_data.author.avatar_url if post_data.author else None
                },
                'created_at': post_data.created_at.isoformat() if post_data.created_at else None,
                'scraped_at': post_data.scraped_at.isoformat() if hasattr(post_data, 'scraped_at') and post_data.scraped_at else datetime.now().isoformat(),
                'metrics': {
                    'likes': post_data.metrics.likes if post_data.metrics else 0,
                    'shares': post_data.metrics.shares if post_data.metrics else 0,
                    'comments': post_data.metrics.comments if post_data.metrics else 0,
                    'views': post_data.metrics.views if post_data.metrics else None
                },
                'media': downloaded_media,
                'scraped_hashtags': post_data.scraped_hashtags if hasattr(post_data, 'scraped_hashtags') else [],
                # NEW: User attribution and hashtags
                'telegram_user': {
                    'user_id': user_context.telegram_user_id if user_context else None,
                    'username': user_context.telegram_username if user_context else None,
                    'first_name': user_context.first_name if user_context else None,
                    'last_name': user_context.last_name if user_context else None
                } if user_context else None,
                'user_notes': user_context.notes if user_context and user_context.notes else None,
                'user_hashtags': user_hashtags or [],
                'download_stats': {
                    'total_media': len(downloaded_media),
                    'successful_downloads': len([m for m in downloaded_media if m.get('local_path')]),
                    'failed_downloads': len([m for m in downloaded_media if m.get('download_error')])
                }
            }
            
            # Save to JSON file
            filename = f"tweet_{post_data.id}.json" if platform.value == 'twitter' else f"{platform.value}_{post_data.id}.json"
            filepath = data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(post_dict, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Saved {platform.value} post {post_data.id} to {filepath}")
            
            # Also save to database
            # Add user hashtags to post before saving
            if user_hashtags:
                post_data.user_hashtags = user_hashtags
            
            # Also save to database
            if database_storage.save_post(post_data):
                logger.info(f"Saved {platform.value} post {post_data.id} to database")
            else:
                logger.warning(f"Failed to save {platform.value} post {post_data.id} to database")
            return post_dict
            
        except Exception as e:
            logger.error(f"Failed to save post to JSON: {e}")
            return None
    async def _send_success_response(self, update: Update, platform, post_data, user_hashtags: list, processing_msg, json_result=None):
        """Send detailed success response with proper SocialMediaPost object access"""
        try:
            # Access SocialMediaPost object attributes directly
            author_username = post_data.author.username if post_data.author else 'Unknown'
            author_name = post_data.author.display_name if post_data.author else 'Unknown'
            post_id = post_data.id
            tweet_text = post_data.text
            created_at = post_data.created_at
            
            # Get metrics from the metrics object
            likes = post_data.metrics.likes if post_data.metrics else 0
            retweets = post_data.metrics.shares if post_data.metrics else 0  # shares is retweets for Twitter
            replies = post_data.metrics.comments if post_data.metrics else 0
            
            # Prepare text display
            if len(tweet_text) > 100:
                display_text = tweet_text[:100] + "..."
            else:
                display_text = tweet_text
            
            # Build response parts
            response_parts = [
                "✅ Tweet scraped successfully!" if platform.value == 'twitter' else f"✅ {platform.value.title()} scraped successfully!",
                "",
                f"👤 Author: @{author_username} ({author_name})",
                f"📅 Date: {created_at}",
                f"👍 Likes: {likes} | 🔄 Retweets: {retweets} | 💬 Replies: {replies}",
                "",
                f"Text: {display_text}",
                "",
            ]
            
            # Add media download links if available
            if json_result and isinstance(json_result, dict) and 'media' in json_result:
                            media_links = []
                            downloaded_media = json_result.get('media', [])
                            
                            for i, media_info in enumerate(downloaded_media):
                                # Skip thumbnails and audio for video platforms
                                if platform.value in ['facebook', 'tiktok']:
                                    # For Facebook: skip thumbnails after videos
                                    if (platform.value == 'facebook' and 
                                        media_info.get('type') == 'photo' and 
                                        i > 0 and any(m.get('type') == 'video' for m in downloaded_media[:i])):
                                        continue
                                    # For TikTok: only show video, skip photo and audio
                                    if (platform.value == 'tiktok' and 
                                        media_info.get('type') in ['photo', 'audio'] and
                                        any(m.get('type') == 'video' for m in downloaded_media)):
                                        continue
                                    
                                if media_info.get('hosted_url'):
                                    media_type = media_info.get('type', 'file').lower()
                                    if media_type in ['photo', 'image']:
                                        icon = "🖼️"
                                    elif media_type in ['video', 'animated_gif']:
                                        icon = "🎥"
                                    else:
                                        icon = "📎"
                                    
                                    # Use local hosted URL instead of original
                                    url = media_info['hosted_url']
                                    media_links.append(f'{icon} <a href="{url}">Download {media_type.title()} {len(media_links)+1}</a>')
                                elif media_info.get('url'):
                                    # Fallback to original URL if local download failed
                                    media_type = media_info.get('type', 'file').lower()
                                    if media_type in ['photo', 'image']:
                                        icon = "🖼️"
                                    elif media_type in ['video', 'animated_gif']:
                                        icon = "🎥"
                                    else:
                                        icon = "📎"
                                    media_links.append(f'{icon} <a href="{media_info["url"]}">Download {media_type.title()} {len(media_links)+1}</a>')
            if media_links:
                    response_parts.extend([
                        "",
                        "📥 Media Downloads:"
                    ])
                    response_parts.extend([f"  {link}" for link in media_links])
            
            # Add JSON storage link
            response_parts.extend([
                "",
                f'💾 <a href="https://ov-ab103a.infomaniak.ch/data/{platform.value}_{post_id}.json">View archived data</a>' if platform.value != "twitter" else f'💾 <a href="https://ov-ab103a.infomaniak.ch/data/tweet_{post_id}.json">View archived data</a>'
            ])
            
            # Join response parts
            response_text = "\n".join(response_parts)
            
            # Send response
            await processing_msg.edit_text(response_text, parse_mode="HTML", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error sending detailed success response: {e}")
            # Fallback to simple message
            simple_message = f"✅ {platform.value.title()} content archived successfully!\n\nPost ID: {post_data.id}\nAuthor: {post_data.author.display_name if post_data.author else 'Unknown'}"
            await processing_msg.edit_text(simple_message)

    async def _send_error_response(self, update: Update, platform, error, processing_msg):
        """Send error response"""
        error_message = f"""❌ **{platform.value.title()} Archive Failed**

**Error:** {error}

**🔧 What you can try:**
• Check if the URL is accessible and public
• Try again in a few minutes (rate limiting)
• Ensure the post still exists

**💡 Need help?** Send /help for supported formats."""
        
        try:
            await processing_msg.edit_text(error_message, parse_mode='Markdown')
        except Exception:
            # Fallback without markdown
            simple_error = f"❌ {platform.value.title()} Archive Failed\n\nError: {error}\n\nTry again later or contact support."
            await processing_msg.edit_text(simple_error)

    async def webhook_handler(self, request):
        """Handle incoming webhook requests"""
        try:
            body = await request.text()
            update = Update.de_json(json.loads(body), self.application.bot)
            await self.application.process_update(update)
            return web.Response(text="OK")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.Response(text="Error", status=500)

    async def start_bot(self):
        """Start the bot in webhook mode"""
        logger.info("Starting bot in WEBHOOK mode")
        
        # Initialize application
        await self.application.initialize()
        await self.application.start()
        
        # Set webhook
        await self.application.bot.set_webhook(url=self.webhook_url)
        logger.info(f"Webhook set to: {self.webhook_url}")
        
        # Create web app
        app = web.Application()
        app.router.add_post('/webhook', self.webhook_handler)
        
        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.webhook_port)
        await site.start()
        
        logger.info(f"Webhook server started on port {self.webhook_port}")
        
        # Get supported platforms
        platforms = self.platform_manager.get_supported_platforms()
        logger.info(f"Multi-platform support: {', '.join(platforms)}")
        
        # Keep running
        while True:
            await asyncio.sleep(1)

async def main():
    """Main function"""
    bot = MultiPlatformBot()
    await bot.start_bot()

if __name__ == "__main__":
    asyncio.run(main())
