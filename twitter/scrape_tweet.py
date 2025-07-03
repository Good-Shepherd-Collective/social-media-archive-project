#!/usr/bin/env python3
"""
Scrape a specific tweet by URL and save it
"""

import asyncio
import json
import os
from datetime import datetime
from twscrape import API
from dotenv import load_dotenv

load_dotenv()

async def scrape_tweet_by_url(url: str):
    api = API()
    
    # Extract tweet ID from URL
    tweet_id = int(url.split('/')[-1].split('?')[0])
    
    try:
        print(f"Scraping tweet ID: {tweet_id}")
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
                'url': f"https://x.com/{tweet.user.username}/status/{tweet.id}",
                'scraped_at': str(datetime.now())
            }
            
            print("✅ Tweet scraped successfully!")
            print(f"📝 Author: @{tweet_data['author']} ({tweet_data['author_name']})")
            print(f"📅 Date: {tweet_data['created_at']}")
            print(f"💬 Text: {tweet_data['text']}")
            print(f"👍 Likes: {tweet_data['like_count']}")
            print(f"🔄 Retweets: {tweet_data['retweet_count']}")
            print(f"💬 Replies: {tweet_data['reply_count']}")
            
            # Save to JSON
            filename = f"tweet_{tweet_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(tweet_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Tweet saved to: {filename}")
            return tweet_data
            
        else:
            print("❌ Tweet not found or not accessible")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping tweet: {e}")
        return None

if __name__ == "__main__":
    # Get URL from command line argument or use default
    import sys
    
    if len(sys.argv) > 1:
        tweet_url = sys.argv[1]
    else:
        tweet_url = input("Enter tweet URL: ")
    
    result = asyncio.run(scrape_tweet_by_url(tweet_url))
    if result:
        print("\n🎉 Scraping completed successfully!")
    else:
        print("\n💥 Scraping failed!")