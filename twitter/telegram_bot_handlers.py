#!/usr/bin/env python3
"""
Telegram Bot Handler Functions for Twitter Scraping
"""

import asyncio
import logging
import os
import json
from storage_utils import storage_manager
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
from twscrape import API

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global API instance
api = API()

async def setup_twitter_account():
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
        accounts = await api.pool.accounts_info()
        for acc in accounts:
            if acc['username'] == username and acc['active']:
                logger.info(f"Twitter account {username} is already active")
                return True
        
        # Add account with cookies
        await api.pool.add_account(
            username, password, email, email_password, cookies=cookies
        )
        logger.info(f"Twitter account {username} added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Twitter account: {e}")
        return False

async def scrape_tweet(url: str) -> dict:
    """Scrape a single tweet by URL"""
    try:
        # Extract tweet ID from URL
        tweet_id = int(url.split('/')[-1].split('?')[0])
        logger.info(f"Attempting to scrape tweet ID: {tweet_id}")
        
        # Scrape tweet
        tweet = await api.tweet_details(tweet_id)
        
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
            
                # Save to file(s) using storage manager
                saved_paths = storage_manager.save_tweet_data(tweet_data, str(tweet_id))
                
                if saved_paths:
                    logger.info(f"Tweet {tweet_id} scraped and saved to {len(saved_paths)} location(s)")
                    tweet_data["saved_paths"] = saved_paths
            return tweet_data
        else:
            logger.warning(f"Tweet not found or not accessible: {url}")
            return None
            
    except Exception as e:
        logger.error(f"Error scraping tweet {url}: {e}")
        return None

def is_authorized(user_id: str) -> bool:
    """Check if user is authorized to use the bot"""
    authorized_users = os.getenv('TELEGRAM_AUTHORIZED_USERS', '').split(',')
    if not authorized_users or authorized_users == ['']:
        return True  # If no restrictions set, allow all users
    return str(user_id) in authorized_users

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "🐦 **Twitter Scraper Bot**\n\n"
        "Send me a Twitter/X URL and I'll scrape it for you!\n\n"
        "**Commands:**\n"
        "/start - Show this help message\n"
        "/status - Check bot status\n\n"
        "**Usage:**\n"
        "Just send a tweet URL like:\n"
        "`https://x.com/username/status/123456789`",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    try:
        accounts = await api.pool.accounts_info()
        active_accounts = [acc for acc in accounts if acc['active']]
        
        status_msg = f"🤖 **Bot Status**\n\n"
        status_msg += f"✅ Bot is running\n"
        status_msg += f"🐦 Active Twitter accounts: {len(active_accounts)}\n"
        
        if active_accounts:
            for acc in active_accounts:
                status_msg += f"  • @{acc['username']}\n"
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        await update.message.reply_text("❌ Error checking bot status")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages (tweet URLs)"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    message_text = update.message.text
    
    # Check if message contains a Twitter/X URL
    if not any(domain in message_text for domain in ['twitter.com', 'x.com']):
        await update.message.reply_text(
            "❌ Please send a valid Twitter/X URL\n"
            "Example: `https://x.com/username/status/123456789`",
            parse_mode='Markdown'
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
    
    # Setup Twitter account if needed
    await setup_twitter_account()
    
    # Send processing message
    processing_msg = await update.message.reply_text("🔄 Scraping tweet...")
    
    try:
        # Scrape the tweet
        tweet_data = await scrape_tweet(tweet_url)
        
        if tweet_data:
            # Send success message with tweet details - use plain text to avoid parsing issues
            clean_text = tweet_data['text'].replace('\n', ' ')[:200]
            if len(tweet_data['text']) > 200:
                clean_text += '...'
            
            success_msg = (
                f"✅ Tweet scraped successfully!\n\n"
                f"👤 Author: @{tweet_data['author']} ({tweet_data['author_name']})\n"
                f"📅 Date: {tweet_data['created_at']}\n"
                f"👍 Likes: {tweet_data['like_count']}\n"
                f"🔄 Retweets: {tweet_data['retweet_count']}\n"
                f"💬 Replies: {tweet_data['reply_count']}\n\n"
                f"Text:\n{clean_text}\n\n"
                f"💾 Saved to: tweet_{tweet_data['id']}.json"
            )
            
            await processing_msg.edit_text(success_msg)
        else:
            await processing_msg.edit_text("❌ Failed to scrape tweet. It may be private or deleted.")
            
    except Exception as e:
        logger.error(f"Error processing tweet URL {tweet_url}: {e}")
        await processing_msg.edit_text(f"❌ Error occurred while scraping tweet: {str(e)}")