import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

def handle_tweet_url(update: Update, context):
    url = update.message.text
    if 'twitter.com' in url or 'x.com' in url:
        # Run your scraper here
        result = your_scraper_function(url)
        update.message.reply_text(f"Results: {result}")

app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.TEXT, handle_tweet_url))
app.run_polling()