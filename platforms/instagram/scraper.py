"""
Instagram scraper implementation using the modular architecture
Based on FaustRen/instagram-posts-scraper but adapted for our system
"""

import re
import logging
from typing import Optional, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json

from core.base_scraper import BaseScraper
from core.data_models import (
    Platform, SocialMediaPost, UserContext, AuthorInfo, 
    PostMetrics, MediaItem, MediaType
)
from core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class InstagramScraper(BaseScraper):
    """Instagram platform scraper with media download support"""
    
    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        self.session = requests.Session()
        # Set up Instagram-specific headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    @property
    def url_patterns(self) -> List[str]:
        """Instagram URL patterns"""
        return [
            r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)/?',
            r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)/?',
            r'https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)/?',
            r'https?://instagram\.com/p/([A-Za-z0-9_-]+)/?',
            r'https?://instagram\.com/reel/([A-Za-z0-9_-]+)/?'
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract post ID from Instagram URL"""
        for pattern in self.url_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract Instagram post ID from URL: {url}")
    
    async def scrape_post(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Scrape an Instagram post"""
        try:
            # Extract post ID
            post_id = self.extract_post_id(url)
            
            logger.debug(f"Scraping Instagram post ID: {post_id}")
            
            # Get post data from Instagram
            post_data = await self._fetch_instagram_post(url)
            
            if not post_data:
                logger.warning(f"No Instagram post data returned for ID: {post_id}")
                return None
            
            # Create base post object
            post = self.create_post_base(post_id, url, user_context)
            
            # Fill in Instagram-specific data
            post.text = post_data.get('caption', '')
            post.created_at = datetime.fromisoformat(post_data.get('timestamp', datetime.now().isoformat()))
            
            # Author information
            author_data = post_data.get('author', {})
            post.author = AuthorInfo(
                username=author_data.get('username', ''),
                display_name=author_data.get('full_name', ''),
                followers_count=author_data.get('followers_count', 0),
                verified=author_data.get('is_verified', False),
                profile_url=f"https://instagram.com/{author_data.get('username', '')}",
                avatar_url=author_data.get('profile_pic_url', '')
            )
            
            # Metrics
            post.metrics = PostMetrics(
                likes=post_data.get('like_count', 0),
                shares=0,  # Instagram doesn't provide share count
                comments=post_data.get('comment_count', 0),
                views=post_data.get('view_count', None)  # Only available for videos
            )
            
            # Extract hashtags from caption
            post.scraped_hashtags = self._extract_hashtags_from_text(post.text)
            
            # Extract media
            post.media = self._extract_media(post_data)
            
            # Store raw Instagram data
            post.raw_data = {
                'post_id': post_id,
                'shortcode': post_data.get('shortcode', post_id),
                'typename': post_data.get('__typename', ''),
                'is_video': post_data.get('is_video', False),
                'accessibility_caption': post_data.get('accessibility_caption', ''),
                'location': post_data.get('location', {}),
                'taken_at_timestamp': post_data.get('taken_at_timestamp', 0),
                'scraped_at': datetime.now().isoformat(),
                'scraped_by_user': user_context.telegram_username if user_context else None,
                'scraped_by_user_id': user_context.telegram_user_id if user_context else None
            }
            
            logger.info(f"Successfully scraped Instagram post {post_id} with {len(post.media)} media items")
            return post
            
        except Exception as e:
            logger.error(f"Failed to scrape Instagram post from {url}: {e}")
            raise ScrapingError(f"Instagram scraping failed: {str(e)}", self.platform_name, url)
    
    async def _fetch_instagram_post(self, url: str) -> Optional[dict]:
        """Fetch Instagram post data using web scraping"""
        try:
            # Make request to Instagram
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find JSON data in script tags
            script_tags = soup.find_all('script', type='text/javascript')
            
            for script in script_tags:
                if script.string and 'window._sharedData' in script.string:
                    # Extract JSON data from window._sharedData
                    json_text = script.string
                    start = json_text.find('window._sharedData = ') + len('window._sharedData = ')
                    end = json_text.find(';</script>', start)
                    if end == -1:
                        end = json_text.find(';', start)
                    
                    json_data = json.loads(json_text[start:end])
                    
                    # Navigate to post data
                    entry_data = json_data.get('entry_data', {})
                    post_page = entry_data.get('PostPage', [])
                    
                    if post_page and len(post_page) > 0:
                        graphql = post_page[0].get('graphql', {})
                        shortcode_media = graphql.get('shortcode_media', {})
                        
                        if shortcode_media:
                            return self._parse_instagram_post_data(shortcode_media)
            
            # Fallback: Try newer Instagram structure
            for script in script_tags:
                if script.string and '"PostPage"' in script.string:
                    try:
                        # Try to extract from newer format
                        return self._parse_modern_instagram_format(script.string)
                    except:
                        continue
            
            logger.warning("Could not find Instagram post data in page")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Instagram post: {e}")
            raise
    
    def _parse_instagram_post_data(self, post_data: dict) -> dict:
        """Parse Instagram post data from GraphQL response"""
        owner = post_data.get('owner', {})
        
        return {
            'shortcode': post_data.get('shortcode', ''),
            'caption': self._extract_caption(post_data),
            'timestamp': datetime.fromtimestamp(post_data.get('taken_at_timestamp', 0)).isoformat(),
            'like_count': post_data.get('edge_media_preview_like', {}).get('count', 0),
            'comment_count': post_data.get('edge_media_to_comment', {}).get('count', 0),
            'view_count': post_data.get('video_view_count'),
            'is_video': post_data.get('is_video', False),
            'display_url': post_data.get('display_url', ''),
            'video_url': post_data.get('video_url', ''),
            'author': {
                'username': owner.get('username', ''),
                'full_name': owner.get('full_name', ''),
                'followers_count': owner.get('edge_followed_by', {}).get('count', 0),
                'is_verified': owner.get('is_verified', False),
                'profile_pic_url': owner.get('profile_pic_url', '')
            },
            'media_items': self._extract_carousel_media(post_data),
            'taken_at_timestamp': post_data.get('taken_at_timestamp', 0),
            'accessibility_caption': post_data.get('accessibility_caption', ''),
            'location': post_data.get('location', {}),
            '__typename': post_data.get('__typename', '')
        }
    
    def _parse_modern_instagram_format(self, script_content: str) -> dict:
        """Parse newer Instagram JSON format"""
        # This is a placeholder for handling newer Instagram formats
        # Implementation would depend on the current Instagram structure
        logger.warning("Modern Instagram format parsing not yet implemented")
        return {}
    
    def _extract_caption(self, post_data: dict) -> str:
        """Extract caption from Instagram post data"""
        caption_edges = post_data.get('edge_media_to_caption', {}).get('edges', [])
        if caption_edges and len(caption_edges) > 0:
            return caption_edges[0].get('node', {}).get('text', '')
        return ''
    
    def _extract_carousel_media(self, post_data: dict) -> List[dict]:
        """Extract media items from carousel posts"""
        media_items = []
        
        # Single image/video
        if post_data.get('display_url'):
            media_items.append({
                'url': post_data.get('display_url'),
                'is_video': post_data.get('is_video', False),
                'video_url': post_data.get('video_url', '')
            })
        
        # Carousel items
        carousel_media = post_data.get('edge_sidecar_to_children', {}).get('edges', [])
        for edge in carousel_media:
            node = edge.get('node', {})
            media_items.append({
                'url': node.get('display_url', ''),
                'is_video': node.get('is_video', False),
                'video_url': node.get('video_url', '')
            })
        
        return media_items
    
    def _extract_hashtags_from_text(self, text: str) -> List[str]:
        """Extract hashtags from Instagram caption"""
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        return [f"#{tag}" for tag in hashtags]
    
    def _extract_media(self, post_data: dict) -> List[MediaItem]:
        """Extract media items from Instagram post with enhanced metadata"""
        media_items = []
        
        try:
            # Handle single media item
            if post_data.get('display_url'):
                if post_data.get('is_video') and post_data.get('video_url'):
                    # Video content
                    media_items.append(MediaItem(
                        url=post_data['video_url'],
                        media_type=MediaType.VIDEO,
                        width=None,
                        height=None,
                        mime_type='video/mp4'
                    ))
                else:
                    # Image content
                    media_items.append(MediaItem(
                        url=post_data['display_url'],
                        media_type=MediaType.PHOTO,
                        width=None,
                        height=None,
                        mime_type='image/jpeg'
                    ))
            
            # Handle carousel media
            carousel_items = post_data.get('media_items', [])
            for item in carousel_items:
                if item.get('is_video') and item.get('video_url'):
                    media_items.append(MediaItem(
                        url=item['video_url'],
                        media_type=MediaType.VIDEO,
                        width=None,
                        height=None,
                        mime_type='video/mp4'
                    ))
                elif item.get('url'):
                    media_items.append(MediaItem(
                        url=item['url'],
                        media_type=MediaType.PHOTO,
                        width=None,
                        height=None,
                        mime_type='image/jpeg'
                    ))
        
        except Exception as e:
            logger.warning(f"Error extracting media from Instagram post: {e}")
        
        return media_items
