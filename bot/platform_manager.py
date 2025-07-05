"""
Platform manager to handle different social media scrapers
"""

import asyncio
import inspect
from typing import Optional, Dict
from urllib.parse import urlparse

from core.data_models import Platform, SocialMediaPost, UserContext
from platforms.twitter.scraper import TwitterScraper
from platforms.instagram.scraper import InstagramScraper
# from platforms.facebook.scraper import FacebookScraper
from platforms.facebook.scraper import FacebookScraper
from platforms.tiktok.scraper import TikTokScraper
# from platforms.tiktok.scraper import TikTokScraper

class PlatformManager:
    """Manages different platform scrapers"""
    
    def __init__(self):
        self.scrapers = {
            'twitter': TwitterScraper(),
            'instagram': InstagramScraper(),
            'facebook': FacebookScraper(),
            'tiktok': TikTokScraper(),
        }
        
        # URL patterns to platform mapping
        self.url_patterns = {
            'twitter.com': 'twitter',
            'x.com': 'twitter',
            'instagram.com': 'instagram',
            'facebook.com': 'facebook',
            'fb.com': 'facebook',
            'tiktok.com': 'tiktok',
        }
    
    def detect_platform(self, url: str) -> Optional[Platform]:
        """Detect platform from URL"""
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        for pattern, platform_name in self.url_patterns.items():
            if pattern in domain:
                return Platform(platform_name)
        
        return None
    
    def get_scraper_for_url(self, url: str):
        """Get appropriate scraper for URL"""
        platform = self.detect_platform(url)
        if platform:
            return self.scrapers.get(platform.value)
        return None
    
    def get_scraper(self, platform: Platform):
        """Get scraper for specific platform"""
        return self.scrapers.get(platform.value)
    
    def get_supported_platforms(self):
        """Get list of supported platforms"""
        return list(self.scrapers.keys())
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is from a supported platform"""
        return self.detect_platform(url) is not None
    
    async def scrape_url(self, url: str, user_context=None):
        """Scrape URL using appropriate platform scraper"""
        scraper = self.get_scraper_for_url(url)
        if scraper:
            # Check if the scraper method is async
            if inspect.iscoroutinefunction(scraper.scrape_post):
                return await scraper.scrape_post(url, user_context)
            else:
                # Run sync method in executor to avoid blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, scraper.scrape_post, url, user_context)
        raise ValueError(f"No scraper available for URL: {url}")

# Global instance
platform_manager = PlatformManager()
