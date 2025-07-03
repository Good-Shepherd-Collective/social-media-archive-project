#!/usr/bin/env python3
"""
Data Verification Script
Run this locally to check what data was stored on the server
"""

import json
import os
import sys
from datetime import datetime, timedelta
import glob

def find_recent_tweets(hours=24):
    """Find tweets scraped in the last N hours"""
    print(f"🔍 Looking for tweets scraped in the last {hours} hours...")
    
    # Look in common locations
    search_paths = [
        ".",
        "./scraped_data",
        "./twitter",
        "scraped_data",
        "twitter"
    ]
    
    recent_tweets = []
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for path in search_paths:
        if os.path.exists(path):
            pattern = os.path.join(path, "tweet_*.json")
            for filename in glob.glob(pattern):
                try:
                    # Check file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
                    if mod_time > cutoff_time:
                        recent_tweets.append((filename, mod_time))
                except:
                    continue
    
    return sorted(recent_tweets, key=lambda x: x[1], reverse=True)

def display_tweet_data(filename):
    """Display tweet data in a formatted way"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📄 File: {filename}")
        print(f"📅 File created: {datetime.fromtimestamp(os.path.getmtime(filename))}")
        print(f"📏 File size: {os.path.getsize(filename)} bytes")
        print(f"🆔 Tweet ID: {data.get('id', 'Unknown')}")
        print(f"👤 Author: @{data.get('author', 'Unknown')} ({data.get('author_name', 'Unknown')})")
        print(f"📝 Text: {data.get('text', 'No text')[:100]}{'...' if len(data.get('text', '')) > 100 else ''}")
        print(f"📅 Created: {data.get('created_at', 'Unknown')}")
        print(f"📊 Engagement:")
        print(f"   👍 Likes: {data.get('like_count', 0)}")
        print(f"   🔄 Retweets: {data.get('retweet_count', 0)}")
        print(f"   💬 Replies: {data.get('reply_count', 0)}")
        print(f"   👀 Views: {data.get('view_count', 'N/A')}")
        print(f"🔗 URL: {data.get('url', 'Unknown')}")
        print(f"⏰ Scraped: {data.get('scraped_at', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 SOCIAL MEDIA ARCHIVE DATA VERIFICATION")
    print("=" * 60)
    
    # Check command line arguments
    hours = 24
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            print("Invalid hours argument, using default of 24 hours")
    
    # Find recent tweets
    recent_tweets = find_recent_tweets(hours)
    
    if not recent_tweets:
        print(f"❌ No tweets found in the last {hours} hours")
        print("\n💡 Tips:")
        print("   - Make sure you're in the project directory")
        print("   - Check if any tweets were actually scraped recently")
        print("   - Try increasing the time range: python verify_data.py 72")
        return
    
    print(f"✅ Found {len(recent_tweets)} recent tweet(s)")
    
    # Display each tweet
    for i, (filename, mod_time) in enumerate(recent_tweets, 1):
        print(f"\n{'='*40} TWEET {i} {'='*40}")
        display_tweet_data(filename)
    
    print(f"\n{'='*60}")
    print(f"✅ Data verification complete!")
    print(f"📊 Total tweets found: {len(recent_tweets)}")
    print(f"🕐 Time range: Last {hours} hours")

if __name__ == "__main__":
    main()
