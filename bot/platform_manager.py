"""
Platform manager for routing URLs to appropriate scrapers
Enhanced with Instagram support
"""

import re
from typing import Optional, Dict, Type
from core.base_scraper import BaseScraper
from platforms.twitter.scraper import TwitterScraper
from platforms.instagram.scraper import InstagramScraper

class PlatformManager:
    """Manages different social media platform scrapers"""
    
    def __init__(self):
        self.scrapers: Dict[str, BaseScraper] = {
            'twitter': TwitterScraper(),
            'instagram': InstagramScraper(),
        }
        
        # URL patterns for platform detection
        self.platform_patterns = {
            'twitter': [
                r'https?://(?:www\.)?(?:twitter\.com|x\.com)/',
                r'https?://t\.co/'
            ],
            'instagram': [
                r'https?://(?:www\.)?instagram\.com/'
            ],
            'facebook': [
                r'https?://(?:www\.)?facebook\.com/',
                r'https?://(?:www\.)?fb\.com/'
            ],
            'tiktok': [
                r'https?://(?:www\.)?tiktok\.com/',
                r'https?://vm\.tiktok\.com/'
            ]
        }
    
    def detect_platform(self, url: str) -> Optional[str]:
        """Detect which platform a URL belongs to"""
        for platform, patterns in self.platform_patterns.items():
            for pattern in patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return platform
        return None
    
    def get_scraper(self, platform: str) -> Optional[BaseScraper]:
        """Get scraper for specified platform"""
        return self.scrapers.get(platform.lower())
    
    def get_scraper_for_url(self, url: str) -> Optional[BaseScraper]:
        """Get appropriate scraper for a given URL"""
        platform = self.detect_platform(url)
        if platform:
            return self.get_scraper(platform)
        return None
    
    def get_supported_platforms(self) -> list:
        """Get list of platforms with active scrapers"""
        return list(self.scrapers.keys())
    
    def is_url_supported(self, url: str) -> bool:
        """Check if URL is supported by any scraper"""
        return self.detect_platform(url) is not None
    
    async def scrape_url(self, url: str, user_context=None):
        """Scrape URL using appropriate platform scraper"""
        scraper = self.get_scraper_for_url(url)
        if scraper:
            return await scraper.scrape_post(url, user_context)
        raise ValueError(f"No scraper available for URL: {url}")

# Global instance
platform_manager = PlatformManager()
