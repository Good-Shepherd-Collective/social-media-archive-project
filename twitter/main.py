#!/usr/bin/env python3
"""
Social Media Archive Project - Twitter Scraper
Uses twscrape library to scrape tweets from Twitter/X
"""

import asyncio
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from twscrape import API, gather
from dotenv import load_dotenv
import os

load_dotenv()

class TwitterScraper:
    def __init__(self):
        self.api = API()
    
    async def setup_accounts(self):
        """Setup Twitter accounts for scraping using environment variables"""
        print("Setting up Twitter accounts...")
        
        # Get credentials from environment
        username = os.getenv('TWITTER_USERNAME')
        password = os.getenv('TWITTER_PASSWORD')
        email = os.getenv('TWITTER_EMAIL')
        email_password = os.getenv('TWITTER_EMAIL_PASSWORD')
        auth_token = os.getenv('AUTH_TOKEN')
        ct0 = os.getenv('CT0')
        
        if not all([username, password, email, email_password, auth_token, ct0]):
            print("Error: Missing credentials in .env file")
            print("Please check your .env file contains all required variables")
            return False
        
        # Format cookies
        cookies = f"auth_token={auth_token}; ct0={ct0}"
        
        try:
            # Check if account already exists
            accounts = await self.api.pool.accounts_info()
            existing_account = None
            for acc in accounts:
                if acc['username'] == username:
                    existing_account = acc
                    break
            
            if existing_account:
                if existing_account['active']:
                    print(f"Account {username} is already active")
                    return True
                else:
                    print(f"Account {username} exists but is not active, removing and re-adding...")
                    await self.api.pool.delete_accounts(username)
            
            # Add account with cookies
            await self.api.pool.add_account(
                username, password, email, email_password, cookies=cookies
            )
            
            # Check if account is active
            accounts = await self.api.pool.accounts_info()
            for acc in accounts:
                if acc['username'] == username:
                    if acc['active']:
                        print(f"Account {username} is now active")
                        return True
                    else:
                        print(f"Account {username} was added but is not active")
                        return False
            
            print("Account setup failed")
            return False
            
        except Exception as e:
            print(f"Error setting up account: {e}")
            return False
    
    async def scrape_tweets_by_query(self, query: str, limit: int = 100) -> List[Dict]:
        """Scrape tweets by search query"""
        print(f"Scraping tweets for query: {query}")
        tweets = []
        
        async for tweet in self.api.search(query, limit=limit):
            tweet_data = {
                'id': tweet.id,
                'text': tweet.rawContent,
                'author': tweet.user.username,
                'author_name': tweet.user.displayname,
                'created_at': tweet.date,
                'retweet_count': tweet.retweetCount,
                'like_count': tweet.likeCount,
                'reply_count': tweet.replyCount,
                'quote_count': tweet.quoteCount,
                'url': f"https://twitter.com/{tweet.user.username}/status/{tweet.id}"
            }
            tweets.append(tweet_data)
        
        return tweets
    
    async def scrape_user_tweets(self, username: str, limit: int = 100) -> List[Dict]:
        """Scrape tweets from a specific user"""
        print(f"Scraping tweets from user: {username}")
        tweets = []
        
        async for tweet in self.api.user_tweets(username, limit=limit):
            tweet_data = {
                'id': tweet.id,
                'text': tweet.rawContent,
                'author': tweet.user.username,
                'author_name': tweet.user.displayname,
                'created_at': tweet.date,
                'retweet_count': tweet.retweetCount,
                'like_count': tweet.likeCount,
                'reply_count': tweet.replyCount,
                'quote_count': tweet.quoteCount,
                'url': f"https://twitter.com/{tweet.user.username}/status/{tweet.id}"
            }
            tweets.append(tweet_data)
        
        return tweets
    
    async def scrape_tweet_by_url(self, url: str) -> Optional[Dict]:
        """Scrape a single tweet by URL"""
        print(f"Scraping tweet from URL: {url}")
        
        # Extract tweet ID from URL
        tweet_id = url.split('/')[-1].split('?')[0]
        
        try:
            tweet = await self.api.tweet_details(int(tweet_id))
            if tweet:
                return {
                    'id': tweet.id,
                    'text': tweet.rawContent,
                    'author': tweet.user.username,
                    'author_name': tweet.user.displayname,
                    'created_at': tweet.date,
                    'retweet_count': tweet.retweetCount,
                    'like_count': tweet.likeCount,
                    'reply_count': tweet.replyCount,
                    'quote_count': tweet.quoteCount,
                    'url': url
                }
        except Exception as e:
            print(f"Error scraping tweet: {e}")
        
        return None
    
    def save_to_json(self, data: List[Dict], filename: str = None):
        """Save scraped data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Data saved to {filename}")
    
    def save_to_csv(self, data: List[Dict], filename: str = None):
        """Save scraped data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tweets_{timestamp}.csv"
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f"Data saved to {filename}")

async def main():
    scraper = TwitterScraper()
    
    # Setup accounts
    if not await scraper.setup_accounts():
        print("Please setup accounts first using twscrape commands")
        return
    
    print("\nTwitter Scraper Options:")
    print("1. Search tweets by query")
    print("2. Scrape user tweets")
    print("3. Scrape single tweet by URL")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == '1':
        query = input("Enter search query: ")
        limit = int(input("Enter number of tweets to scrape (default 100): ") or 100)
        tweets = await scraper.scrape_tweets_by_query(query, limit)
        
    elif choice == '2':
        username = input("Enter username (without @): ")
        limit = int(input("Enter number of tweets to scrape (default 100): ") or 100)
        tweets = await scraper.scrape_user_tweets(username, limit)
        
    elif choice == '3':
        url = input("Enter tweet URL: ")
        tweet = await scraper.scrape_tweet_by_url(url)
        tweets = [tweet] if tweet else []
        
    else:
        print("Invalid choice")
        return
    
    if tweets:
        print(f"\nScraped {len(tweets)} tweets")
        
        # Save options
        save_format = input("Save as JSON or CSV? (json/csv): ").lower()
        if save_format == 'csv':
            scraper.save_to_csv(tweets)
        else:
            scraper.save_to_json(tweets)
    else:
        print("No tweets found")

if __name__ == "__main__":
    asyncio.run(main())