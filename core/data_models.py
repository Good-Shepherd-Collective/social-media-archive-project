"""
Unified data models for all social media platforms
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class Platform(Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"

class MediaType(Enum):
    PHOTO = "photo"
    VIDEO = "video"
    ANIMATED_GIF = "animated_gif"
    AUDIO = "audio"

@dataclass
class MediaItem:
    """Represents a media file (image, video, etc.)"""
    url: str
    media_type: MediaType
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # For videos/audio
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    local_path: Optional[str] = None
    hosted_url: Optional[str] = None

@dataclass
class UserContext:
    """User attribution information from Telegram"""
    telegram_user_id: int
    telegram_username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'telegram_user_id': self.telegram_user_id,
            'telegram_username': self.telegram_username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'notes': self.notes
        }

@dataclass
class AuthorInfo:
    """Information about the post author"""
    username: str
    display_name: str
    followers_count: Optional[int] = None
    verified: bool = False
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None

@dataclass
class PostMetrics:
    """Engagement metrics for a post"""
    likes: int = 0
    shares: int = 0  # retweets, reposts, etc.
    comments: int = 0
    views: Optional[int] = None
    saves: Optional[int] = None  # bookmarks, saves
    
    def to_dict(self) -> Dict[str, int]:
        return {
            'likes': self.likes,
            'shares': self.shares,
            'comments': self.comments,
            'views': self.views,
            'saves': self.saves
        }

@dataclass
class SocialMediaPost:
    """Unified model for social media posts across all platforms"""
    # Core identification
    id: str
    platform: Platform
    url: str
    
    # Content
    text: str
    author: AuthorInfo
    
    # Timestamps
    created_at: datetime
    scraped_at: datetime
    
    # Media and engagement
    media: List[MediaItem] = field(default_factory=list)
    metrics: PostMetrics = field(default_factory=PostMetrics)
    
    # Hashtags
    scraped_hashtags: List[str] = field(default_factory=list)  # From original post
    user_hashtags: List[str] = field(default_factory=list)     # Added by user
    
    # User attribution
    user_context: Optional[UserContext] = None
    
    # Platform-specific data
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'platform': self.platform.value,
            'url': self.url,
            'text': self.text,
            'author': {
                'username': self.author.username,
                'display_name': self.author.display_name,
                'followers_count': self.author.followers_count,
                'verified': self.author.verified,
                'profile_url': self.author.profile_url,
                'avatar_url': self.author.avatar_url
            },
            'created_at': self.created_at.isoformat(),
            'scraped_at': self.scraped_at.isoformat(),
            'media': [
                {
                    'url': item.url,
                    'type': item.media_type.value,
                    'width': item.width,
                    'height': item.height,
                    'duration': item.duration,
                    'file_size': item.file_size,
                    'mime_type': item.mime_type,
                    'local_path': item.local_path,
                    'hosted_url': item.hosted_url
                } for item in self.media
            ],
            'metrics': self.metrics.to_dict(),
            'scraped_hashtags': self.scraped_hashtags,
            'user_hashtags': self.user_hashtags,
            'user_context': self.user_context.to_dict() if self.user_context else None,
            'raw_data': self.raw_data
        }
    
    def get_filename(self) -> str:
        """Generate filename for JSON storage"""
        return f"{self.platform.value}_{self.id}.json"
