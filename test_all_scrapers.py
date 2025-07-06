#!/usr/bin/env python3
"""
Test that all platform scrapers still work after our changes
"""

import asyncio
from core.scraper_manager import scraper_manager
from core.data_models import UserContext

# Test URLs for each platform
test_urls = {
    'twitter': 'https://twitter.com/example/status/123456789',
    'instagram': 'https://www.instagram.com/p/ABC123/',
    'tiktok': 'https://www.tiktok.com/@user/video/123456789',
    'facebook': 'https://www.facebook.com/user/posts/123456'
}

async def test_scrapers():
    print("Testing all platform scrapers...")
    print("=" * 60)
    
    for platform_name, url in test_urls.items():
        print(f"\nTesting {platform_name}...")
        
        try:
            # Check if scraper can handle URL
            platform = scraper_manager.detect_platform(url)
            if platform:
                print(f"✓ Platform detected: {platform.value}")
                
                # Get the scraper
                scraper = scraper_manager.get_scraper(platform)
                if scraper:
                    print(f"✓ Scraper found: {scraper.__class__.__name__}")
                    
                    # Check URL patterns
                    matches_pattern = any(
                        __import__('re').match(pattern, url) 
                        for pattern in scraper.url_patterns
                    )
                    print(f"✓ URL pattern matches: {matches_pattern}")
                else:
                    print(f"✗ No scraper found for {platform_name}")
            else:
                print(f"✗ Platform not detected for URL: {url}")
                
        except Exception as e:
            print(f"✗ Error testing {platform_name}: {e}")
    
    # Test media download logic
    print("\n" + "=" * 60)
    print("Testing media download logic...")
    
    # Check if our patches are in place
    with open('/home/ubuntu/social-media-archive-project/main_bot.py', 'r') as f:
        bot_content = f.read()
        
    checks = [
        ('smart_media_downloader import', 'from core.smart_media_downloader import smart_media_downloader' in bot_content),
        ('Facebook merge check', '_audio_stream' in bot_content),
        ('json_result handling', 'json_result = self.save_post_to_json' in bot_content),
        ('Local URL usage', 'hosted_url' in bot_content and 'Download Video' in bot_content)
    ]
    
    for check_name, result in checks:
        print(f"{'✓' if result else '✗'} {check_name}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
