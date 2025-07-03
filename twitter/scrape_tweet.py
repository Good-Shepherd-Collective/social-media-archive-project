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
            # Extract media if available
            media_data = []
            if hasattr(tweet, 'media') and tweet.media:
                for media_item in tweet.media:
                    media_url = None
                    if hasattr(media_item, 'variants') and media_item.variants:
                        # Find the highest bitrate variant for videos
                        best_variant = max(media_item.variants, key=lambda v: v.get('bitrate', 0) if v.get('bitrate') else 0)
                        media_url = best_variant.get('url')
                    elif hasattr(media_item, 'url'):
                        media_url = media_item.url
                    
                    if media_url:
                        media_data.append({
                            'url': media_url,
                            'type': media_item.type, # e.g., 'photo', 'video', 'animated_gif'
                            'width': getattr(media_item, 'width', None),
                            'height': getattr(media_item, 'height', None)
                        })
            
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
                'media': media_data, # Add media data to tweet
                'scraped_at': str(datetime.now())
            }
            
            print("✅ Tweet scraped successfully!")
            print(f"📝 Author: @{tweet_data['author']} ({tweet_data['author_name']})")
            print(f"📅 Date: {tweet_data['created_at']}")
            print(f"💬 Text: {tweet_data['text']}")
            print(f"👍 Likes: {tweet_data['like_count']}")
            print(f"🔄 Retweets: {tweet_data['retweet_count']}")
            print(f"💬 Replies: {tweet_data['reply_count']}")
            if tweet_data['media']:
                print(f"📷 Media files: {len(tweet_data['media'])}")
                for i, media in enumerate(tweet_data['media']):
                    print(f"   {i+1}. {media['type']}: {media['url']}")
            
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