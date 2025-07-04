"""
Platform manager for coordinating different social media scrapers
"""

import logging
from typing import Dict, Optional, List
import asyncio

from core.data_models import Platform, SocialMediaPost, UserContext
from core.base_scraper import BaseScraper
from core.storage_manager import UnifiedStorageManager
from core.exceptions import PlatformNotSupportedError, ScrapingError
from .url_detector import URLDetector

logger = logging.getLogger(__name__)

class PlatformManager:
    """Manages all platform scrapers and coordinates scraping operations"""
    
    def __init__(self, storage_manager: Optional[UnifiedStorageManager] = None):
        self.url_detector = URLDetector()
        self.storage_manager = storage_manager or UnifiedStorageManager()
        self.scrapers: Dict[Platform, BaseScraper] = {}
        self._register_scrapers()
    
    def _register_scrapers(self):
        """Register all available platform scrapers"""
        # Import and register scrapers
        try:
            from platforms.twitter.scraper import TwitterScraper
            self.scrapers[Platform.TWITTER] = TwitterScraper()
            logger.info("Registered Twitter scraper")
        except ImportError as e:
            logger.warning(f"Could not register Twitter scraper: {e}")
        
        try:
            from platforms.facebook.scraper import FacebookScraper
            self.scrapers[Platform.FACEBOOK] = FacebookScraper()
            logger.info("Registered Facebook scraper")
        except ImportError as e:
            logger.warning(f"Could not register Facebook scraper: {e}")
        
        try:
            from platforms.instagram.scraper import InstagramScraper
            self.scrapers[Platform.INSTAGRAM] = InstagramScraper()
            logger.info("Registered Instagram scraper")
        except ImportError as e:
            logger.warning(f"Could not register Instagram scraper: {e}")
        
        try:
            from platforms.tiktok.scraper import TikTokScraper
            self.scrapers[Platform.TIKTOK] = TikTokScraper()
            logger.info("Registered TikTok scraper")
        except ImportError as e:
            logger.warning(f"Could not register TikTok scraper: {e}")
    
    def get_scraper(self, platform: Platform) -> BaseScraper:
        """Get scraper for a specific platform"""
        if platform not in self.scrapers:
            raise PlatformNotSupportedError(f"No scraper available for {platform.value}")
        return self.scrapers[platform]
    
    def get_available_platforms(self) -> List[Platform]:
        """Get list of platforms with registered scrapers"""
        return list(self.scrapers.keys())
    
    async def scrape_url(self, url: str, user_hashtags: List[str] = None, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """
        Scrape a URL using the appropriate platform scraper
        
        Args:
            url: URL to scrape
            user_hashtags: User-provided hashtags
            user_context: User attribution information
            
        Returns:
            SocialMediaPost or None if scraping failed
            
        Raises:
            PlatformNotSupportedError: If platform is not supported
            ScrapingError: If scraping fails
        """
        # Detect platform
        platform = self.url_detector.detect_platform(url)
        if not platform:
            raise PlatformNotSupportedError(f"URL {url} is not from a supported platform")
        
        # Get appropriate scraper
        scraper = self.get_scraper(platform)
        
        # Scrape the post
        logger.info(f"Scraping {platform.value} URL: {url}")
        post = await scraper.scrape_with_attribution(url, user_hashtags, user_context)
        
        if post:
            logger.info(f"Successfully scraped {platform.value} post {post.id}")
        else:
            logger.warning(f"Failed to scrape {platform.value} URL: {url}")
        
        return post
    
    async def scrape_and_save(self, url: str, user_hashtags: List[str] = None, user_context: Optional[UserContext] = None) -> Dict[str, any]:
        """
        Scrape a URL and save it to storage
        
        Args:
            url: URL to scrape
            user_hashtags: User-provided hashtags
            user_context: User attribution information
            
        Returns:
            Dictionary with scraping results
        """
        result = {
            'success': False,
            'platform': None,
            'post_id': None,
            'saved_paths': [],
            'error': None
        }
        
        try:
            # Scrape the post
            post = await self.scrape_url(url, user_hashtags, user_context)
            
            if post:
                # Save to storage
                saved_paths = self.storage_manager.save_post(post)
                
                result.update({
                    'success': True,
                    'platform': post.platform.value,
                    'post_id': post.id,
                    'saved_paths': saved_paths,
                    'post_data': post.to_dict()
                })
                
                logger.info(f"Successfully scraped and saved {post.platform.value} post {post.id}")
            else:
                result['error'] = "Scraping returned no data"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Failed to scrape and save URL {url}: {e}")
        
        return result
    
    def parse_message(self, message_text: str) -> Dict[str, any]:
        """
        Parse a message to extract URLs and hashtags
        
        Args:
            message_text: The message text to parse
            
        Returns:
            Dictionary with parsed data
        """
        urls = self.url_detector.extract_urls(message_text)
        hashtags = self.url_detector.extract_hashtags(message_text)
        
        # Filter to supported URLs only
        supported_urls = []
        for url in urls:
            if self.url_detector.is_supported_url(url):
                platform = self.url_detector.detect_platform(url)
                supported_urls.append({
                    'url': url,
                    'platform': platform.value if platform else None
                })
        
        return {
            'urls': supported_urls,
            'hashtags': hashtags,
            'has_supported_urls': len(supported_urls) > 0
        }
    
    def get_status_info(self) -> Dict[str, any]:
        """Get status information about registered scrapers"""
        status = {
            'available_platforms': [p.value for p in self.get_available_platforms()],
            'supported_platforms': self.url_detector.get_supported_platforms(),
            'scrapers': {},
            'storage': self.storage_manager.get_storage_info()
        }
        
        for platform, scraper in self.scrapers.items():
            status['scrapers'][platform.value] = {
                'class': scraper.__class__.__name__,
                'url_patterns': len(scraper.url_patterns)
            }
        
        return status

# Global instance
platform_manager = PlatformManager()
