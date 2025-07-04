"""
Twitter scraper implementation using the modular architecture
Enhanced with media downloading capabilities
"""

import re
import logging
from typing import Optional, List
from datetime import datetime
from twscrape import API

from core.base_scraper import BaseScraper
from core.data_models import (
    Platform, SocialMediaPost, UserContext, AuthorInfo, 
    PostMetrics, MediaItem, MediaType
)
from core.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    """Twitter/X platform scraper with media download support"""
    
    def __init__(self):
        super().__init__(Platform.TWITTER)
        self.api = API()
    
    @property
    def url_patterns(self) -> List[str]:
        """Twitter URL patterns"""
        return [
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://(?:www\.)?(?:mobile\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://t\.co/\w+'
        ]
    
    def extract_post_id(self, url: str) -> str:
        """Extract tweet ID from Twitter URL"""
        # Handle t.co short URLs by following redirects
        if 't.co' in url:
            # For now, extract the last part and assume it contains the ID
            # In production, you might want to follow the redirect
            pass
        
        # Extract ID from standard Twitter URLs
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        
        raise ValueError(f"Could not extract tweet ID from URL: {url}")
    
    async def scrape_post(self, url: str, user_context: Optional[UserContext] = None) -> Optional[SocialMediaPost]:
        """Scrape a Twitter post with enhanced media handling"""
        try:
            # Extract tweet ID
            tweet_id = int(self.extract_post_id(url))
            
            logger.debug(f"Scraping Twitter post ID: {tweet_id}")
            
            # Get tweet details using twscrape
            tweet = await self.api.tweet_details(tweet_id)
            
            if not tweet:
                logger.warning(f"No tweet data returned for ID: {tweet_id}")
                return None
            
            # Create base post object
            post = self.create_post_base(str(tweet_id), url, user_context)
            
            # Fill in tweet-specific data
            post.text = tweet.rawContent or ""
            post.created_at = tweet.date
            
            # Author information
            post.author = AuthorInfo(
                username=tweet.user.username,
                display_name=tweet.user.displayname,
                followers_count=tweet.user.followersCount,
                verified=tweet.user.verified,
                profile_url=f"https://x.com/{tweet.user.username}",
                avatar_url=tweet.user.profileImageUrl if hasattr(tweet.user, 'profileImageUrl') else None
            )
            
            # Metrics
            post.metrics = PostMetrics(
                likes=tweet.likeCount or 0,
                shares=tweet.retweetCount or 0,  # Retweets are shares
                comments=tweet.replyCount or 0,
                views=getattr(tweet, 'viewCount', None)
            )
            
            # Extract hashtags from text
            post.scraped_hashtags = self._extract_hashtags_from_text(post.text)
            
            # Extract media with enhanced metadata
            post.media = self._extract_media(tweet)
            
            # Store raw Twitter data
            post.raw_data = {
                'tweet_id': tweet.id,
                'conversation_id': getattr(tweet, 'conversationId', None),
                'in_reply_to': getattr(tweet, 'inReplyToTweetId', None),
                'lang': getattr(tweet, 'lang', None),
                'source': getattr(tweet, 'source', None),
                'quote_count': getattr(tweet, 'quoteCount', 0),
                'bookmark_count': getattr(tweet, 'bookmarkCount', None),
                'user_id': tweet.user.id,
                'user_created': getattr(tweet.user, 'created', None),
                'user_location': getattr(tweet.user, 'location', None),
                'user_description': getattr(tweet.user, 'description', None),
                'user_verified_type': getattr(tweet.user, 'verifiedType', None),
                'scraped_at': datetime.now().isoformat(),
                'scraped_by_user': user_context.telegram_username if user_context else None,
                'scraped_by_user_id': user_context.telegram_user_id if user_context else None
            }
            
            logger.info(f"Successfully scraped Twitter post {tweet_id} with {len(post.media)} media items")
            return post
            
        except Exception as e:
            logger.error(f"Failed to scrape Twitter post from {url}: {e}")
            raise ScrapingError(f"Twitter scraping failed: {str(e)}", self.platform_name, url)
    
    def _extract_hashtags_from_text(self, text: str) -> List[str]:
        """Extract hashtags from tweet text"""
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        return [f"#{tag}" for tag in hashtags]
    
    def _extract_media(self, tweet) -> List[MediaItem]:
        """Extract media items from tweet with enhanced metadata"""
        media_items = []
        
        if not hasattr(tweet, 'media') or not tweet.media:
            return media_items
        
        try:
            # Process photos
            if hasattr(tweet.media, 'photos') and tweet.media.photos:
                for photo in tweet.media.photos:
                    media_url = None
                    
                    if hasattr(photo, 'url'):
                        media_url = photo.url
                    elif hasattr(photo, 'variants') and photo.variants:
                        # Find best quality variant
                        best_variant = max(photo.variants, 
                                         key=lambda v: getattr(v, "bitrate", 0) if getattr(v, "bitrate", None) else 0)
                        media_url = getattr(best_variant, "url", None)
                    
                    if media_url:
                        # Enhance URL to get highest quality
                        if '?format=' in media_url:
                            # Try to get original quality
                            media_url = media_url.replace('&name=small', '&name=orig')
                            media_url = media_url.replace('&name=medium', '&name=orig')
                            media_url = media_url.replace('&name=large', '&name=orig')
                        
                        media_items.append(MediaItem(
                            url=media_url,
                            media_type=MediaType.PHOTO,
                            width=getattr(photo, 'width', None),
                            height=getattr(photo, 'height', None),
                            mime_type='image/jpeg'  # Default for Twitter photos
                        ))
            
            # Process videos
            if hasattr(tweet.media, 'videos') and tweet.media.videos:
                for video in tweet.media.videos:
                    media_url = None
                    
                    if hasattr(video, 'variants') and video.variants:
                        # Find best quality variant (highest bitrate)
                        video_variants = [v for v in video.variants 
                                        if getattr(v, 'contentType', '').startswith('video/')]
                        if video_variants:
                            best_variant = max(video_variants,
                                             key=lambda v: getattr(v, "bitrate", 0) if getattr(v, "bitrate", None) else 0)
                            media_url = getattr(best_variant, "url", None)
                    
                    if media_url:
                        media_items.append(MediaItem(
                            url=media_url,
                            media_type=MediaType.VIDEO,
                            width=getattr(video, 'width', None),
                            height=getattr(video, 'height', None),
                            duration=getattr(video, 'duration', None),
                            mime_type='video/mp4'  # Default for Twitter videos
                        ))
            
            # Process animated GIFs
            if hasattr(tweet.media, 'animated') and tweet.media.animated:
                for gif in tweet.media.animated:
                    media_url = None
                    
                    if hasattr(gif, 'variants') and gif.variants:
                        # For GIFs, prefer mp4 format
                        mp4_variants = [v for v in gif.variants 
                                      if getattr(v, 'contentType', '') == 'video/mp4']
                        if mp4_variants:
                            best_variant = max(mp4_variants,
                                             key=lambda v: getattr(v, "bitrate", 0) if getattr(v, "bitrate", None) else 0)
                            media_url = getattr(best_variant, "url", None)
                        else:
                            # Fallback to any variant
                            media_url = getattr(gif.variants[0], 'url', None) if gif.variants else None
                    else:
                        media_url = getattr(gif, 'url', None)
                    
                    if media_url:
                        media_items.append(MediaItem(
                            url=media_url,
                            media_type=MediaType.ANIMATED_GIF,
                            width=getattr(gif, 'width', None),
                            height=getattr(gif, 'height', None),
                            mime_type='video/mp4'  # Twitter GIFs are usually mp4
                        ))
        
        except Exception as e:
            logger.warning(f"Error extracting media from tweet: {e}")
        
        return media_items
