"""
Abstract base class for all social media platform scrapers
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import re
import logging
from datetime import datetime

from .data_models import SocialMediaPost, UserContext, Platform
from .exceptions import ScrapingError, PlatformNotSupportedError

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all platform scrapers"""
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.platform_name = platform.value
        
    @property
    @abstractmethod
    def url_patterns(self) -> List[str]:
        """Return list of regex patterns that match this platform's URLs"""
        pass
    
    @abstractmethod
    async def scrape_post(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """
        Scrape a post from the platform
        
        Args:
            url: The URL of the post to scrape
            user_context: User attribution information
            
        Returns:
            SocialMediaPost object or None if scraping failed
            
        Raises:
            ScrapingError: If scraping fails
        """
        pass
    
    @abstractmethod
    def extract_post_id(self, url: str) -> str:
        """
        Extract post ID from URL
        
        Args:
            url: The URL to extract ID from
            
        Returns:
            String post ID
            
        Raises:
            ValueError: If URL format is invalid
        """
        pass
    
    def detect_url(self, url: str) -> bool:
        """
        Check if URL belongs to this platform
        
        Args:
            url: The URL to check
            
        Returns:
            True if URL matches this platform
        """
        for pattern in self.url_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def validate_url(self, url: str) -> bool:
        """
        Validate that URL is supported by this scraper
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is valid and supported
            
        Raises:
            PlatformNotSupportedError: If URL doesn't match this platform
        """
        if not self.detect_url(url):
            raise PlatformNotSupportedError(
                f"URL {url} is not supported by {self.platform_name} scraper"
            )
        return True
    
    def create_post_base(self, post_id: str, url: str, user_context: Optional[UserContext] = None) -> SocialMediaPost:
        """
        Create a base SocialMediaPost object with common fields
        
        Args:
            post_id: The post ID
            url: The post URL
            user_context: User attribution information
            
        Returns:
            Partially populated SocialMediaPost object
        """
        from .data_models import SocialMediaPost, AuthorInfo, PostMetrics
        
        return SocialMediaPost(
            id=post_id,
            platform=self.platform,
            url=url,
            text="",  # To be filled by specific scraper
            author=AuthorInfo(username="", display_name=""),  # To be filled
            created_at=datetime.now(),  # To be filled with actual date
            scraped_at=datetime.now(),
            user_context=user_context,
            metrics=PostMetrics()
        )
    
    async def scrape_with_attribution(self, url: str, user_hashtags: List[str] = None, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """
        Scrape a post with user attribution and hashtags
        
        Args:
            url: The URL to scrape
            user_hashtags: User-provided hashtags
            user_context: User attribution information
            
        Returns:
            SocialMediaPost with user attribution
        """
        try:
            # Validate URL
            self.validate_url(url)
            
            # Scrape the post
            post = await self.scrape_post(url, user_context)
            
            if post and user_hashtags:
                post.user_hashtags = user_hashtags
            
            logger.info(f"Successfully scraped {self.platform_name} post {post.id if post else 'FAILED'}")
            return post
            
        except Exception as e:
            logger.error(f"Failed to scrape {self.platform_name} post from {url}: {e}")
            raise ScrapingError(f"Failed to scrape {self.platform_name} post: {str(e)}", self.platform_name, url)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.platform_name})"
    
    def __repr__(self) -> str:
        return self.__str__()
