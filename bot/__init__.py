"""
Telegram bot module for handling multi-platform social media scraping
"""

from .url_detector import URLDetector
from .platform_manager import PlatformManager

__all__ = ['URLDetector', 'PlatformManager']
