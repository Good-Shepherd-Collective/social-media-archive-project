"""
Instagram scraper implementation with multiple fallback methods
Uses public Instagram endpoints to avoid GraphQL restrictions
"""

import re
import time
import json
import logging
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import instaloader
from urllib.parse import quote

from core.base_scraper import BaseScraper
from core.data_models import (
    Platform, SocialMediaPost, UserContext, AuthorInfo, 
    PostMetrics, MediaItem, MediaType
)
from core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class InstagramScraper(BaseScraper):
    """Instagram platform scraper with multiple fallback methods"""
    
    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        
        # Initialize instaloader as fallback
        self.loader = instaloader.Instaloader(
            sleep=True,
            quiet=True,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            max_connection_attempts=1,
            request_timeout=30.0,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
        )
        
        # Setup for public API method
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0
        
    @property
    def url_patterns(self) -> List[str]:
        """Instagram URL patterns"""
        return [
            r'https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract post ID (shortcode) from Instagram URL - REQUIRED ABSTRACT METHOD"""
        for pattern in self.url_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ScrapingError(f"Could not extract post ID from URL: {url}")
    
    def scrape_post(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Scrape Instagram post - REQUIRED ABSTRACT METHOD"""
        return self.scrape_url(url, user_context)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _extract_shortcode(self, url: str) -> str:
        """Extract shortcode from Instagram URL"""
        return self.extract_post_id(url)
    
    def _scrape_with_public_api(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """Try to scrape using Instagram's public JSON endpoint"""
        try:
            self._rate_limit()
            
            # Instagram's public post endpoint
            url = f"https://www.instagram.com/p/{shortcode}/"
            
            logger.info(f"Fetching Instagram post via public API: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Extract JSON data from the page
                html_content = response.text
                
                # Look for the JSON data in the HTML
                json_pattern = r'window\._sharedData\s*=\s*({.+?});'
                json_match = re.search(json_pattern, html_content)
                
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        logger.info("✅ Successfully extracted data from public API")
                        return data
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse JSON from public API")
                
                # Alternative: Look for newer Instagram data structure
                json_pattern_alt = r'<script type="application/ld\+json">({.+?})</script>'
                json_matches = re.findall(json_pattern_alt, html_content)
                
                for json_match in json_matches:
                    try:
                        data = json.loads(json_match)
                        if 'author' in data or 'caption' in data:
                            logger.info("✅ Successfully extracted data from LD+JSON")
                            return data
                    except json.JSONDecodeError:
                        continue
                        
            elif response.status_code == 403:
                logger.warning("Public API also blocked with 403 Forbidden")
                return None
            else:
                logger.warning(f"Public API returned status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Public API method failed: {e}")
            return None
    
    def _scrape_with_instaloader(self, shortcode: str) -> Optional[instaloader.Post]:
        """Try to scrape using instaloader as fallback"""
        try:
            self._rate_limit()
            
            logger.info(f"Fetching Instagram post via instaloader: {shortcode}")
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            logger.info("✅ Successfully fetched post with instaloader")
            return post
            
        except instaloader.exceptions.QueryReturnedNotFoundException:
            logger.error(f"Instagram post not found: {shortcode}")
            return None
        except instaloader.exceptions.BadResponseException as e:
            logger.warning(f"Instagram API error: {e}")
            return None
        except instaloader.exceptions.PostChangedException:
            logger.warning(f"Instagram post has been changed: {shortcode}")
            return None
        except Exception as e:
            logger.warning(f"Instaloader method failed: {e}")
            return None
    
    def _extract_post_data_from_public_api(self, data: Dict[str, Any], shortcode: str) -> Optional[Dict[str, Any]]:
        """Extract post data from public API response"""
        try:
            # Try to find post data in the response
            if 'entry_data' in data and 'PostPage' in data['entry_data']:
                post_data = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']
                return self._normalize_post_data(post_data)
            
            # Alternative data structure
            if 'author' in data and 'caption' in data:
                # This is LD+JSON format
                return {
                    'id': shortcode,
                    'shortcode': shortcode,
                    'caption': data.get('caption', ''),
                    'author': data.get('author', {}).get('name', ''),
                    'author_username': data.get('author', {}).get('url', '').split('/')[-1],
                    'timestamp': data.get('datePublished', ''),
                    'media_type': 'image',
                    'media_url': data.get('image', ''),
                    'like_count': 0,
                    'comment_count': 0,
                    'is_video': False
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract post data from public API: {e}")
            return None
    
    def _normalize_post_data(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize post data to common format"""
        try:
            return {
                'id': post_data.get('id', ''),
                'shortcode': post_data.get('shortcode', ''),
                'caption': post_data.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                'author': post_data.get('owner', {}).get('full_name', ''),
                'author_username': post_data.get('owner', {}).get('username', ''),
                'timestamp': datetime.fromtimestamp(post_data.get('taken_at_timestamp', 0)).isoformat(),
                'media_type': 'video' if post_data.get('is_video', False) else 'image',
                'media_url': post_data.get('display_url', ''),
                'like_count': post_data.get('edge_media_preview_like', {}).get('count', 0),
                'comment_count': post_data.get('edge_media_to_comment', {}).get('count', 0),
                'is_video': post_data.get('is_video', False)
            }
        except Exception as e:
            logger.warning(f"Failed to normalize post data: {e}")
            return {}
    
    def _convert_instaloader_post(self, post: instaloader.Post) -> Dict[str, Any]:
        """Convert instaloader post to common format"""
        try:
            return {
                'id': post.mediaid,
                'shortcode': post.shortcode,
                'caption': post.caption or '',
                'author': post.owner_profile.full_name or '',
                'author_username': post.owner_username,
                'timestamp': post.date.isoformat(),
                'media_type': 'video' if post.is_video else 'image',
                'media_url': post.url,
                'like_count': post.likes,
                'comment_count': post.comments,
                'is_video': post.is_video
            }
        except Exception as e:
            logger.warning(f"Failed to convert instaloader post: {e}")
            return {}
    
    def scrape_url(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Scrape Instagram URL using multiple fallback methods"""
        try:
            shortcode = self._extract_shortcode(url)
            logger.info(f"Extracted shortcode: {shortcode}")
            
            post_data = None
            
            # Method 1: Try public API first
            logger.info("🔄 Trying public API method...")
            public_data = self._scrape_with_public_api(shortcode)
            if public_data:
                post_data = self._extract_post_data_from_public_api(public_data, shortcode)
                if post_data:
                    logger.info("✅ Successfully scraped with public API")
            
            # Method 2: Fallback to instaloader
            if not post_data:
                logger.info("🔄 Trying instaloader method...")
                insta_post = self._scrape_with_instaloader(shortcode)
                if insta_post:
                    post_data = self._convert_instaloader_post(insta_post)
                    if post_data:
                        logger.info("✅ Successfully scraped with instaloader")
            
            # If both methods failed
            if not post_data:
                logger.error("❌ All scraping methods failed")
                return None
            
            # Convert to our data model
            return self._create_social_media_post(post_data, url, user_context)
            
        except Exception as e:
            logger.error(f"Instagram scraping failed: {e}")
            raise ScrapingError(f"Failed to scrape Instagram URL: {e}")
    
    def _create_social_media_post(self, post_data: Dict[str, Any], original_url: str, user_context: Optional[UserContext] = None) -> SocialMediaPost:
        """Create SocialMediaPost from post data"""
        try:
            # Create author info
            author = AuthorInfo(
                username=post_data.get('author_username', ''),
                display_name=post_data.get('author', ''),
                profile_url=f"https://www.instagram.com/{post_data.get('author_username', '')}/",
                avatar_url=None,
                follower_count=None,
                verified=False
            )
            
            # Create metrics
            metrics = PostMetrics(
                likes=post_data.get('like_count', 0),
                comments=post_data.get('comment_count', 0),
                shares=None,
                retweets=None,
                views=None
            )
            
            # Create media items
            media_items = []
            if post_data.get('media_url'):
                media_type = MediaType.VIDEO if post_data.get('is_video', False) else MediaType.IMAGE
                media_items.append(MediaItem(
                    url=post_data['media_url'],
                    type=media_type,
                    thumbnail_url=post_data.get('media_url') if media_type == MediaType.IMAGE else None
                ))
            
            # Parse timestamp
            timestamp = None
            if post_data.get('timestamp'):
                try:
                    timestamp = datetime.fromisoformat(post_data['timestamp'].replace('Z', '+00:00'))
                except:
                    try:
                        timestamp = datetime.fromisoformat(post_data['timestamp'])
                    except:
                        timestamp = datetime.now()
            
            # Create the post
            return SocialMediaPost(
                id=post_data.get('id', post_data.get('shortcode', '')),
                platform=Platform.INSTAGRAM,
                url=original_url,
                author=author,
                content=post_data.get('caption', ''),
                timestamp=timestamp or datetime.now(),
                metrics=metrics,
                media_items=media_items,
                scraped_at=datetime.now(),
                user_context=user_context
            )
            
        except Exception as e:
            logger.error(f"Failed to create SocialMediaPost: {e}")
            raise ScrapingError(f"Failed to create post object: {e}")
