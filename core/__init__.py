"""
Core module for Social Media Archive Project
Provides base classes and shared functionality for all platforms
"""

from .base_scraper import BaseScraper
from .data_models import SocialMediaPost, UserContext, MediaItem, Platform
from .storage_manager import UnifiedStorageManager
from .exceptions import ScrapingError, PlatformNotSupportedError

__all__ = [
    'BaseScraper',
    'SocialMediaPost', 
    'UserContext',
    'MediaItem',
    'Platform',
    'UnifiedStorageManager',
    'ScrapingError',
    'PlatformNotSupportedError'
]
