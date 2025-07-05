"""
URL detection and platform routing for multi-platform support
"""

import re
from typing import Optional, Dict, List
import logging

from core.data_models import Platform
from core.exceptions import PlatformNotSupportedError

logger = logging.getLogger(__name__)

class URLDetector:
    """Detects which platform a URL belongs to"""
    
    # Platform URL patterns
    PLATFORM_PATTERNS = {
        Platform.TWITTER: [
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://(?:www\.)?(?:mobile\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://t\.co/\w+'
        ],
        Platform.FACEBOOK: [
            r'https?://(?:www\.)?facebook\.com/.+/posts/\d+',
            r'https?://(?:www\.)?facebook\.com/permalink\.php\?story_fbid=\d+',
            r'https?://(?:www\.)?fb\.com/\w+',
            r'https?://(?:m\.)?facebook\.com/.+/posts/\d+',
            r'https?://(?:www\.)?facebook\.com/share/[pv]/[\w-]+',
            r'https?://(?:www\.)?facebook\.com/watch/\?v=\d+',
            r'https?://(?:www\.)?facebook\.com/[\w\-\.]+/videos/\d+'
        ],
        Platform.INSTAGRAM: [
            r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/tv/[\w-]+',
            r'https?://instagr\.am/p/[\w-]+'
        ],
        Platform.TIKTOK: [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:v[mt]\.)?tiktok\.com/[\w-]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w-]+',
            r'https?://m\.tiktok\.com/v/\d+'
        ]
    }
    
    def __init__(self):
        self.supported_platforms = list(self.PLATFORM_PATTERNS.keys())
    
    def detect_platform(self, url: str) -> Optional[Platform]:
        """
        Detect which platform a URL belongs to
        
        Args:
            url: The URL to analyze
            
        Returns:
            Platform enum or None if not supported
        """
        url = url.strip()
        
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    logger.debug(f"Detected {platform.value} URL: {url}")
                    return platform
        
        logger.debug(f"No platform detected for URL: {url}")
        return None
    
    def is_supported_url(self, url: str) -> bool:
        """Check if URL is supported by any platform"""
        return self.detect_platform(url) is not None
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        hashtag_pattern = r'#([\w]+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        # Clean hashtags (remove duplicates, lowercase)
        return list(set([tag.lower() for tag in hashtags]))
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platform names"""
        return [platform.value for platform in self.supported_platforms]
    
    def get_platform_examples(self) -> Dict[str, List[str]]:
        """Get example URLs for each platform"""
        examples = {
            Platform.TWITTER.value: [
                "https://twitter.com/user/status/123456",
                "https://x.com/user/status/123456"
            ],
            Platform.FACEBOOK.value: [
                "https://facebook.com/user/posts/123456",
                "https://www.facebook.com/permalink.php?story_fbid=123456"
            ],
            Platform.INSTAGRAM.value: [
                "https://instagram.com/p/ABC123",
                "https://instagram.com/reel/ABC123"
            ],
            Platform.TIKTOK.value: [
                "https://tiktok.com/@user/video/123456",
                "https://vm.tiktok.com/ABC123"
            ]
        }
        return examples
