"""
Facebook scraper using RapidAPI
Supports posts, videos, and photos with video/audio stream merging
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

class FacebookScraper(BaseScraper):
    """Facebook platform scraper using RapidAPI"""
    
    def __init__(self):
        super().__init__(Platform.FACEBOOK)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.rapidapi_host = 'facebook-scraper3.p.rapidapi.com'
        
        if not self.rapidapi_key:
            logger.warning("RAPIDAPI_KEY not found - Facebook scraping will not work")
        
        self.headers = {
            'x-rapidapi-host': self.rapidapi_host,
            'x-rapidapi-key': self.rapidapi_key
        }
    
    @property
    def url_patterns(self) -> List[str]:
        """Facebook URL patterns"""
        return [
            r'https?://(?:www\.)?facebook\.com/[\w\-\.]+/(?:posts|videos|photos)/[\w\-]+',
            r'https?://(?:www\.)?facebook\.com/share/[pv]/[\w\-]+',
            r'https?://(?:www\.)?fb\.com/[\w\-]+',
            r'https?://(?:www\.)?facebook\.com/watch/\?v=\d+',
            r'https?://(?:www\.)?facebook\.com/[\w\-\.]+/videos/\d+',
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract post ID from Facebook URL"""
        # For share URLs like /share/v/192xatZpWN/
        share_match = re.search(r'/share/[pv]/([\w\-]+)', url)
        if share_match:
            return share_match.group(1)
        
        # For video URLs like /videos/734654152588312/
        video_match = re.search(r'/videos/(\d+)', url)
        if video_match:
            return video_match.group(1)
        
        # For watch URLs like /watch/?v=123456
        watch_match = re.search(r'/watch/\?v=(\d+)', url)
        if watch_match:
            return watch_match.group(1)
        
        # For post URLs
        post_match = re.search(r'/posts/([\w\-]+)', url)
        if post_match:
            return post_match.group(1)
        
        # If all else fails, use the entire URL
        return url
    
    def fetch_facebook_content(self, url: str) -> Dict[str, Any]:
        """Fetch Facebook content using RapidAPI"""
        api_url = f"https://{self.rapidapi_host}/post"
        
        try:
            logger.info(f"Fetching Facebook post: {url}")
            
            # URL encode the Facebook URL
            encoded_url = quote(url, safe='')
            
            response = requests.get(
                api_url,
                headers=self.headers,
                params={'post_url': url},  # API expects unencoded URL as param
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"RapidAPI error: {response.status_code} - {response.text}")
                raise ScrapingError(f"Failed to fetch Facebook post: {response.status_code}")
            
            data = response.json()
            
            # Check if we got valid data
            if not data or 'error' in data:
                error_msg = data.get('error', 'Unknown error')
                raise ScrapingError(f"Facebook API error: {error_msg}")
            
            return data.get('results', {})
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise ScrapingError(f"Network error fetching Facebook content: {str(e)}")
    
    def parse_media_items(self, data: Dict[str, Any]) -> List[MediaItem]:
        """Parse media items from Facebook data"""
        media_items = []
        
        # Check post type
        post_type = data.get('type', '')
        
        if post_type in ["video_post", "reel"]:
            # Check for video_representations (the format from your example)
            if 'video_representations' in data:
                video_reps = data['video_representations']
                if video_reps:
                    # Extract best video and audio streams
                    video_streams = [r for r in video_reps if isinstance(r, dict) and r.get('height', 0) > 0]
                    audio_streams = [r for r in video_reps if isinstance(r, dict) and r.get('height', 0) == 0 and 'mp4a' in r.get('codecs', '')]
                    
                    # Mark in raw_data if this needs merging
                    data['_needs_stream_merge'] = bool(video_streams and audio_streams)
                    
                    if video_streams and audio_streams:
                        # We have separate streams - store both for merging
                        # Get best quality video
                        best_video = max(video_streams, key=lambda x: (x.get('height', 0), x.get('bandwidth', 0)))
                        audio_stream = audio_streams[0]  # Usually only one audio stream
                        
                        # Store stream info in raw data for downloader
                        data['_video_stream'] = best_video
                        data['_audio_stream'] = audio_stream
                        
                        # Create a media item for the video (will be handled specially by downloader)
                        media_items.append(MediaItem(
                            url=best_video.get('base_url', ''),
                            media_type=MediaType.VIDEO,
                            width=best_video.get('width'),
                            height=best_video.get('height'),
                            duration=data.get('playable_duration_s')
                        ))
                    elif video_streams:
                        # Only video (might have embedded audio)
                        best_video = max(video_streams, key=lambda x: (x.get('height', 0), x.get('bandwidth', 0)))
                        media_items.append(MediaItem(
                            url=best_video.get('base_url', ''),
                            media_type=MediaType.VIDEO,
                            width=best_video.get('width'),
                            height=best_video.get('height'),
                            duration=data.get('playable_duration_s')
                        ))
                        
            # Check for old format (representations)
            elif 'representations' in data and isinstance(data['representations'], dict):
                reps_data = data['representations'].get('representations', [])
                if reps_data:
                    # Filter out audio-only and get best quality video
                    video_reps = [r for r in reps_data if isinstance(r, dict) and r.get('height', 0) > 0]
                    if video_reps:
                        best_video = max(video_reps, key=lambda x: x.get('bandwidth', 0))
                        media_items.append(MediaItem(
                            url=best_video.get('base_url', ''),
                            media_type=MediaType.VIDEO,
                            width=best_video.get('width'),
                            height=best_video.get('height'),
                            duration=data.get('length_in_second', data.get('playable_duration_s'))
                        ))
            
            # Add thumbnail
            if 'thumbnail_uri' in data:
                media_items.append(MediaItem(
                    url=data['thumbnail_uri'],
                    media_type=MediaType.PHOTO
                ))
        
        elif post_type == 'photo_post':
            # Handle photo posts
            if 'images' in data:
                for img in data['images']:
                    media_items.append(MediaItem(
                        url=img.get('uri', ''),
                        media_type=MediaType.PHOTO,
                        width=img.get('width'),
                        height=img.get('height')
                    ))
        
        # Handle regular posts that have an image field
        if 'image' in data and isinstance(data['image'], dict):
            img = data['image']
            if img.get('uri'):
                media_items.append(MediaItem(
                    url=img.get('uri', ''),
                    media_type=MediaType.PHOTO,
                    width=img.get('width'),
                    height=img.get('height')
                ))
        
        return media_items
    
    def parse_facebook_data(self, data: Dict[str, Any], url: str, 
                           user_context: Optional[UserContext]) -> SocialMediaPost:
        """Parse Facebook data into unified format"""
        
        # Extract author information
        author_info = data.get('author', {})
        author = AuthorInfo(
            username=author_info.get('id', 'unknown'),
            display_name=author_info.get('name', 'Unknown'),
            profile_url=author_info.get('url', '')
        )
        
        # Extract metrics from reactions
        reactions = data.get('reactions', {})
        total_reactions = data.get('reactions_count', 0)
        
        metrics = PostMetrics(
            likes=reactions.get('like', 0) + reactions.get('love', 0),  # Combine positive reactions
            comments=data.get('comments_count', 0),
            shares=data.get('reshare_count', 0),
            views=data.get('play_count')  # For videos
        )
        
        # Get post text
        text = data.get('message', '')
        
        # Extract hashtags from message
        scraped_hashtags = re.findall(r'#(\w+)', text)
        
        # Parse media items
        media_items = self.parse_media_items(data)
        
        # Get post ID and timestamp
        post_id = data.get('post_id', self.extract_post_id(url))
        
        # Convert timestamp
        timestamp = data.get('timestamp')
        if timestamp:
            created_at = datetime.fromtimestamp(int(timestamp))
        else:
            created_at = datetime.now()
        
        # Store reaction breakdown in raw_data
        data['reaction_breakdown'] = reactions
        
        return SocialMediaPost(
            id=post_id,
            platform=Platform.FACEBOOK,
            url=data.get('url', url),
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
        """Scrape Facebook post"""
        try:
            # Fetch data from RapidAPI
            data = self.fetch_facebook_content(url)
            
            # Parse into unified format
            post = self.parse_facebook_data(data, url, user_context)
            
            logger.info(f"Successfully scraped Facebook post {post.id} with "
                       f"{len(post.media)} media items")
            
            return post
            
        except Exception as e:
            logger.error(f"Error scraping Facebook URL {url}: {str(e)}")
            raise ScrapingError(f"Failed to scrape Facebook content: {str(e)}")
    
    def scrape_url(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Main entry point for scraping Facebook URLs"""
        return self.scrape_post(url, user_context)
