#!/usr/bin/env python3
"""
Run the Telegram Bot for Twitter Scraping
This script properly handles the async event loop
"""

import logging
import os
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Add the current directory to path so we can import bot functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    # Import bot functions after setting up the environment
    from telegram_bot_handlers import start_command, status_command, handle_message, setup_twitter_account
    
    # Check for bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    logger.info("Starting Telegram bot...")
    application.run_polling()

if __name__ == "__main__":
    main()