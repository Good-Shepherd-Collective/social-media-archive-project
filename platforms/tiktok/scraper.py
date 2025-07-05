"""
TikTok scraper using RapidAPI
Supports TikTok videos with download capabilities
"""

import re
import os
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse, quote

from core.base_scraper import BaseScraper
from core.data_models import (
    Platform, SocialMediaPost, UserContext, MediaItem, 
    MediaType, AuthorInfo, PostMetrics
)
from core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class TikTokScraper(BaseScraper):
    """TikTok platform scraper using RapidAPI"""
    
    def __init__(self):
        super().__init__(Platform.TIKTOK)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.rapidapi_host = 'tiktok-video-no-watermark2.p.rapidapi.com'
        
        if not self.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not found - TikTok scraping will not work")
        
        self.headers = {
            'x-rapidapi-host': self.rapidapi_host,
            'x-rapidapi-key': self.rapidapi_key
        }
    
    @property
    def url_patterns(self) -> List[str]:
        """TikTok URL patterns"""
        return [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm\.)?tiktok\.com/[\w-]+',
            r'https?://(?:vt\.)?tiktok\.com/[\w-]+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w-]+',
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract post ID from TikTok URL"""
        # For video URLs like /@user/video/123456
        video_match = re.search(r'/video/(\d+)', url)
        if video_match:
            return video_match.group(1)
        
        # For short URLs, use the entire URL as ID
        return url
    
    def fetch_tiktok_content(self, url: str) -> Dict[str, Any]:
        """Fetch TikTok content using RapidAPI"""
        api_url = f"https://{self.rapidapi_host}/"
        
        try:
            logger.info(f"Fetching TikTok video: {url}")
            
            response = requests.get(
                api_url,
                headers=self.headers,
                params={
                    'url': url,
                    'hd': '1'  # Get HD video when available
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"RapidAPI error: {response.status_code} - {response.text}")
                raise ScrapingError(f"Failed to fetch TikTok video: {response.status_code}")
            
            data = response.json()
            
            # Check if we got valid data
            if data.get('code') != 0:
                error_msg = data.get('msg', 'Unknown error')
                raise ScrapingError(f"TikTok API error: {error_msg}")
            
            return data.get('data', {})
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise ScrapingError(f"Network error fetching TikTok content: {str(e)}")
    
    def parse_media_items(self, data: Dict[str, Any]) -> List[MediaItem]:
        """Parse media items from TikTok data"""
        media_items = []
        
        # Get the best quality video available
        video_url = None
        video_size = None
        
        if 'hdplay' in data and data['hdplay']:
            # HD video available
            video_url = data['hdplay']
            video_size = data.get('hd_size')
        elif 'play' in data and data['play']:
            # Standard quality video (no watermark)
            video_url = data['play']
            video_size = data.get('size')
        elif 'wmplay' in data and data['wmplay']:
            # Watermarked video as fallback
            video_url = data['wmplay']
            video_size = data.get('wm_size')
        
        if video_url:
            media_items.append(MediaItem(
                url=video_url,
                media_type=MediaType.VIDEO,
                duration=data.get('duration'),
                file_size=video_size
            ))
        
        # Add cover/thumbnail
        if 'cover' in data:
            media_items.append(MediaItem(
                url=data['cover'],
                media_type=MediaType.PHOTO
            ))
        
        # Add music/audio if available
        if 'music' in data and data['music']:
            media_items.append(MediaItem(
                url=data['music'],
                media_type=MediaType.AUDIO,
                duration=data.get('music_info', {}).get('duration')
            ))
        
        return media_items
    
    def parse_tiktok_data(self, data: Dict[str, Any], url: str, 
                         user_context: Optional[UserContext]) -> SocialMediaPost:
        """Parse TikTok data into unified format"""
        
        # Extract author information
        author_info = data.get('author', {})
        author = AuthorInfo(
            username=author_info.get('unique_id', 'unknown'),
            display_name=author_info.get('nickname', author_info.get('unique_id', 'unknown')),
            profile_url=f"https://www.tiktok.com/@{author_info.get('unique_id', '')}"
        )
        
        # Extract metrics
        metrics = PostMetrics(
            likes=data.get('digg_count', 0),
            comments=data.get('comment_count', 0),
            shares=data.get('share_count', 0),
            views=data.get('play_count', 0),
            saves=data.get('collect_count', 0)  # TikTok's "favorites"
        )
        
        # Get post text/title
        text = data.get('title', '')
        
        # Extract hashtags and mentions from title
        scraped_hashtags = re.findall(r'#(\w+)', text)
        
        # Parse media items
        media_items = self.parse_media_items(data)
        
        # Get post ID
        post_id = data.get('id', data.get('aweme_id', self.extract_post_id(url)))
        
        # Convert timestamp
        create_time = data.get('create_time')
        if create_time:
            created_at = datetime.fromtimestamp(int(create_time))
        else:
            created_at = datetime.now()
        
        # Store additional TikTok-specific data
        data['music_info'] = data.get('music_info', {})
        data['download_count'] = data.get('download_count', 0)
        data['is_ad'] = data.get('is_ad', False)
        
        return SocialMediaPost(
            id=post_id,
            platform=Platform.TIKTOK,
            url=url,
            text=text,
            author=author,
            created_at=created_at,
            scraped_at=datetime.now(),
            media=media_items,
            metrics=metrics,
            scraped_hashtags=scraped_hashtags,
            user_hashtags=[],
            user_context=user_context,
            raw_data=data
        )
    
    def scrape_post(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Scrape TikTok video"""
        try:
            # Fetch data from RapidAPI
            data = self.fetch_tiktok_content(url)
            
            # Parse into unified format
            post = self.parse_tiktok_data(data, url, user_context)
            
            logger.info(f"Successfully scraped TikTok video {post.id} with "
                       f"{len(post.media)} media items")
            
            return post
            
        except Exception as e:
            logger.error(f"Error scraping TikTok URL {url}: {str(e)}")
            raise ScrapingError(f"Failed to scrape TikTok content: {str(e)}")
    
    def scrape_url(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Main entry point for scraping TikTok URLs"""
        return self.scrape_post(url, user_context)
