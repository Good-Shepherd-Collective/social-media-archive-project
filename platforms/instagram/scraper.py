"""
Instagram scraper using RapidAPI
Supports posts, reels, and IGTV content
"""

import re
import os
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from core.base_scraper import BaseScraper
from core.data_models import (
    Platform, SocialMediaPost, UserContext, MediaItem, 
    MediaType, AuthorInfo, PostMetrics
)
from core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class InstagramScraper(BaseScraper):
    """Instagram platform scraper using RapidAPI"""
    
    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.rapidapi_host = os.getenv('RAPIDAPI_INSTAGRAM_HOST', 
                                       'instagram-scrapper-posts-reels-stories-downloader.p.rapidapi.com')
        
        if not self.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not found - Instagram scraping will not work")
        
        self.headers = {
            'x-rapidapi-host': self.rapidapi_host,
            'x-rapidapi-key': self.rapidapi_key
        }
    
    @property
    def url_patterns(self) -> List[str]:
        """Instagram URL patterns"""
        return [
            r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract post ID (shortcode) from Instagram URL"""
        for pattern in self.url_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ScrapingError(f"Could not extract post ID from URL: {url}")
    
    def detect_content_type(self, url: str) -> str:
        """Detect Instagram content type from URL"""
        if '/reel/' in url:
            return 'reel'
        elif '/tv/' in url:
            return 'igtv'
        else:
            return 'post'
    
    def fetch_instagram_content(self, shortcode: str, content_type: str) -> Dict[str, Any]:
        """Fetch Instagram content using appropriate RapidAPI endpoint"""
        endpoint_map = {
            'reel': 'reel_by_shortcode',
            'igtv': 'igtv_by_shortcode',
            'post': 'post_by_shortcode'
        }
        
        endpoint = endpoint_map.get(content_type, 'post_by_shortcode')
        url = f"https://{self.rapidapi_host}/{endpoint}"
        
        try:
            logger.info(f"Fetching Instagram {content_type} with shortcode: {shortcode}")
            response = requests.get(
                url, 
                headers=self.headers,
                params={'shortcode': shortcode},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"RapidAPI error: {response.status_code} - {response.text}")
                raise ScrapingError(f"Failed to fetch Instagram {content_type}: {response.status_code}")
            
            data = response.json()
            
            # Check if we got valid data
            if not data or 'error' in data:
                error_msg = data.get('error', 'Unknown error')
                raise ScrapingError(f"Instagram API error: {error_msg}")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise ScrapingError(f"Network error fetching Instagram content: {str(e)}")
    
    def parse_media_items(self, data: Dict[str, Any]) -> List[MediaItem]:
        """Parse media items from Instagram data"""
        media_items = []
        
        # Check media type
        media_type = data.get('media_type', 1)
        
        if media_type == 1:  # Photo
            # Get best quality image
            if 'image_versions2' in data and 'candidates' in data['image_versions2']:
                candidates = data['image_versions2']['candidates']
                if candidates:
                    # Get the highest resolution version
                    best_image = max(candidates, key=lambda x: x.get('width', 0) * x.get('height', 0))
                    media_items.append(MediaItem(
                        url=best_image['url'],
                        media_type=MediaType.PHOTO,
                        width=best_image.get('width'),
                        height=best_image.get('height')
                    ))
            
        elif media_type == 2:  # Video
            # Get video versions
            if 'video_versions' in data:
                video_versions = data['video_versions']
                if video_versions:
                    # Get the best quality video
                    best_video = video_versions[0]  # Usually ordered by quality
                    media_items.append(MediaItem(
                        url=best_video['url'],
                        media_type=MediaType.VIDEO,
                        width=best_video.get('width'),
                        height=best_video.get('height'),
                        duration=data.get('video_duration')
                    ))
            
            # Also add thumbnail
            if 'image_versions2' in data and 'candidates' in data['image_versions2']:
                candidates = data['image_versions2']['candidates']
                if candidates:
                    thumbnail = candidates[0]
                    media_items.append(MediaItem(
                        url=thumbnail['url'],
                        media_type=MediaType.PHOTO,
                        width=thumbnail.get('width'),
                        height=thumbnail.get('height')
                    ))
        
        elif media_type == 8:  # Carousel (multiple media)
            # Handle carousel media
            if 'carousel_media' in data:
                for item in data['carousel_media']:
                    item_type = item.get('media_type', 1)
                    if item_type == 1:  # Photo
                        if 'image_versions2' in item:
                            candidates = item['image_versions2'].get('candidates', [])
                            if candidates:
                                best_image = max(candidates, key=lambda x: x.get('width', 0) * x.get('height', 0))
                                media_items.append(MediaItem(
                                    url=best_image['url'],
                                    media_type=MediaType.PHOTO,
                                    width=best_image.get('width'),
                                    height=best_image.get('height')
                                ))
                    elif item_type == 2:  # Video
                        if 'video_versions' in item:
                            video = item['video_versions'][0]
                            media_items.append(MediaItem(
                                url=video['url'],
                                media_type=MediaType.VIDEO,
                                width=video.get('width'),
                                height=video.get('height'),
                                duration=item.get('video_duration')
                            ))
        
        return media_items
    
    def parse_instagram_data(self, data: Dict[str, Any], url: str, 
                           user_context: Optional[UserContext]) -> SocialMediaPost:
        """Parse Instagram data into unified format"""
        
        # Extract author information from user field
        user_info = data.get('user', {})
        author = AuthorInfo(
            username=user_info.get('username', 'unknown'),
            display_name=user_info.get('full_name', user_info.get('username', 'unknown')),
            followers_count=user_info.get('follower_count'),
            verified=user_info.get('is_verified', False),
            profile_url=f"https://instagram.com/{user_info.get('username', '')}",
            avatar_url=user_info.get('profile_pic_url')
        )
        
        # Extract metrics
        metrics = PostMetrics(
            likes=data.get('like_count', 0),
            comments=data.get('comment_count', 0),
            views=data.get('view_count') or data.get('play_count'),
            saves=data.get('saved_count')
        )
        
        # Extract caption and hashtags
        caption_data = data.get('caption')
        if caption_data:
            text = caption_data.get('text', '')
        else:
            text = ''
        
        scraped_hashtags = re.findall(r'#(\w+)', text)
        
        # Parse media items
        media_items = self.parse_media_items(data)
        
        # Get post ID and timestamps
        post_id = data.get('code', self.extract_post_id(url))
        
        # Convert timestamp
        taken_at = data.get('taken_at')
        if taken_at:
            created_at = datetime.fromtimestamp(int(taken_at))
        else:
            created_at = datetime.now()
        
        return SocialMediaPost(
            id=post_id,
            platform=Platform.INSTAGRAM,
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
        """Scrape Instagram post/reel/IGTV"""
        try:
            # Extract shortcode and detect content type
            shortcode = self.extract_post_id(url)
            content_type = self.detect_content_type(url)
            
            # Fetch data from RapidAPI
            data = self.fetch_instagram_content(shortcode, content_type)
            
            # Parse into unified format
            post = self.parse_instagram_data(data, url, user_context)
            
            logger.info(f"Successfully scraped Instagram {content_type} {post.id} with "
                       f"{len(post.media)} media items")
            
            return post
            
        except Exception as e:
            logger.error(f"Error scraping Instagram URL {url}: {str(e)}")
            raise ScrapingError(f"Failed to scrape Instagram content: {str(e)}")
    
    def scrape_url(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Main entry point for scraping Instagram URLs"""
        return self.scrape_post(url, user_context)
