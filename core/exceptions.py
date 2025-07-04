"""
Custom exceptions for the Social Media Archive Project
"""

class SocialMediaArchiveException(Exception):
    """Base exception for the social media archive project"""
    pass

class ScrapingError(SocialMediaArchiveException):
    """Raised when scraping fails"""
    def __init__(self, message: str, platform: str = None, url: str = None):
        self.platform = platform
        self.url = url
        super().__init__(message)

class PlatformNotSupportedError(SocialMediaArchiveException):
    """Raised when a platform is not supported"""
    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"Platform '{platform}' is not supported")

class UserAttributionError(SocialMediaArchiveException):
    """Raised when user attribution fails"""
    pass

class StorageError(SocialMediaArchiveException):
    """Raised when storage operations fail"""
    pass

class DatabaseError(SocialMediaArchiveException):
    """Raised when database operations fail"""
    pass

class MediaDownloadError(SocialMediaArchiveException):
    """Raised when media download fails"""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)
