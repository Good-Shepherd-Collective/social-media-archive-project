#!/usr/bin/env python3
"""
Test script for Instagram scraper functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from platforms.instagram.scraper import InstagramScraper
from core.data_models import UserContext

async def test_instagram_scraper():
    """Test Instagram scraper functionality"""
    
    # Initialize scraper
    scraper = InstagramScraper()
    
    print("🧪 Testing Instagram Scraper")
    print("=" * 40)
    print(f"Platform: {scraper.platform_name}")
    print(f"Supported URL patterns: {len(scraper.url_patterns)}")
    
    # Test URL patterns
    test_urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://instagram.com/reel/XYZ789/",
        "https://www.instagram.com/tv/DEF456/"
    ]
    
    print("\n📋 Testing URL pattern matching:")
    for url in test_urls:
        try:
            post_id = scraper.extract_post_id(url)
            print(f"   ✅ {url} -> {post_id}")
        except ValueError as e:
            print(f"   ❌ {url} -> {e}")
    
    # Test with real Instagram URL (if provided)
    test_url = input("\n🔗 Enter an Instagram post URL to test (or press Enter to skip): ").strip()
    
    if test_url:
        try:
            print(f"\n🚀 Testing with URL: {test_url}")
            
            # Create test user context
            user_context = UserContext(
                telegram_user_id=12345,
                telegram_username="test_user",
                first_name="Test",
                notes="Instagram scraper test"
            )
            
            # Attempt to scrape
            post = await scraper.scrape_post(test_url, user_context)
            
            if post:
                print("✅ Scraping successful!")
                print(f"   Post ID: {post.id}")
                print(f"   Author: {post.author.username}")
                print(f"   Text: {post.text[:100]}...")
                print(f"   Media items: {len(post.media)}")
                print(f"   Likes: {post.metrics.likes}")
                print(f"   Comments: {post.metrics.comments}")
            else:
                print("❌ Scraping failed - no data returned")
                
        except Exception as e:
            print(f"❌ Scraping failed with error: {e}")
    else:
        print("⏭️ Skipping real URL test")
    
    print("\n🏁 Instagram scraper test completed!")

if __name__ == "__main__":
    asyncio.run(test_instagram_scraper())
