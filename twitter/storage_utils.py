"""
Storage utilities for Twitter scraper
Enhanced with media downloading capabilities
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

# Add parent directory to path for core imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.media_downloader import media_downloader

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'both')  # Default to 'both'
        self.local_path = os.getenv('LOCAL_STORAGE_PATH', '../scraped_data')
        self.server_path = os.getenv('SERVER_STORAGE_PATH', '/home/ubuntu/social-media-archive-project/scraped_data')
        
        # Database configuration
        self.use_database = os.getenv('USE_DATABASE', 'true').lower() == 'true'
        self.download_media = os.getenv('DOWNLOAD_MEDIA', 'true').lower() == 'true'
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'social_media_archive'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'socialarchive2025'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
    def get_storage_paths(self, filename: str) -> List[str]:
        """Get list of paths where data should be saved based on environment"""
        paths = []
        
        if self.environment == 'local':
            paths.append(os.path.join(self.local_path, filename))
        elif self.environment == 'server':
            paths.append(os.path.join(self.server_path, filename))
        else:  # 'both' or any other value
            paths.append(os.path.join(self.local_path, filename))
            paths.append(os.path.join(self.server_path, filename))
        
        return paths
    
    def save_to_database(self, tweet_data: Dict[Any, Any], user_hashtags: List[str] = None, user_context: dict = None) -> bool:
        """Save tweet data to PostgreSQL database with media download support"""
        if not self.use_database:
            return False
            
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Extract hashtags from tweet text
            scraped_hashtags = []
            if 'text' in tweet_data:
                import re
                hashtag_pattern = r'#\w+'
                scraped_hashtags = re.findall(hashtag_pattern, tweet_data['text'])
            
            # Prepare data for insertion
            insert_data = {
                'id': tweet_data.get('id'),
                'text': tweet_data.get('text'),
                'author': tweet_data.get('author'),
                'author_name': tweet_data.get('author_name'),
                'author_followers': tweet_data.get('author_followers'),
                'author_verified': tweet_data.get('author_verified', False),
                'created_at': tweet_data.get('created_at'),
                'scraped_at': tweet_data.get('scraped_at', str(datetime.now())),
                'retweet_count': tweet_data.get('retweet_count', 0),
                'like_count': tweet_data.get('like_count', 0),
                'reply_count': tweet_data.get('reply_count', 0),
                'quote_count': tweet_data.get('quote_count', 0),
                'view_count': tweet_data.get('view_count'),
                'original_url': tweet_data.get('url'),
                'platform': 'twitter',
                'scraped_by_user': tweet_data.get('scraped_by_user'),
                'user_notes': tweet_data.get('user_notes'),
                'raw_data': Json(tweet_data)
            }
            
            # Add user context data if provided
            if user_context:
                insert_data['scraped_by_user'] = user_context.get('username', tweet_data.get('scraped_by_user'))
                insert_data['scraped_by_user_id'] = user_context.get('user_id')
                insert_data['user_notes'] = user_context.get('notes', tweet_data.get('user_notes'))
            
            # Insert or update tweet
            insert_query = """
                INSERT INTO tweets (
                    id, text, author, author_name, author_followers, author_verified,
                    created_at, scraped_at, retweet_count, like_count, reply_count, 
                    quote_count, view_count, original_url, platform, scraped_by_user,
                    scraped_by_user_id, user_notes, raw_data
                ) VALUES (
                    %(id)s, %(text)s, %(author)s, %(author_name)s, %(author_followers)s, %(author_verified)s,
                    %(created_at)s, %(scraped_at)s, %(retweet_count)s, %(like_count)s, %(reply_count)s,
                    %(quote_count)s, %(view_count)s, %(original_url)s, %(platform)s, %(scraped_by_user)s,
                    %(scraped_by_user_id)s, %(user_notes)s, %(raw_data)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    text = EXCLUDED.text,
                    author = EXCLUDED.author,
                    author_name = EXCLUDED.author_name,
                    author_followers = EXCLUDED.author_followers,
                    author_verified = EXCLUDED.author_verified,
                    created_at = EXCLUDED.created_at,
                    scraped_at = EXCLUDED.scraped_at,
                    retweet_count = EXCLUDED.retweet_count,
                    like_count = EXCLUDED.like_count,
                    reply_count = EXCLUDED.reply_count,
                    quote_count = EXCLUDED.quote_count,
                    view_count = EXCLUDED.view_count,
                    original_url = EXCLUDED.original_url,
                    platform = EXCLUDED.platform,
                    scraped_by_user = EXCLUDED.scraped_by_user,
                    scraped_by_user_id = EXCLUDED.scraped_by_user_id,
                    user_notes = EXCLUDED.user_notes,
                    raw_data = EXCLUDED.raw_data;
            """
            
            cursor.execute(insert_query, insert_data)
            
            # Handle hashtags separately
            tweet_id = tweet_data.get('id')
            
            # Insert user hashtags
            if user_hashtags:
                user_who_added = user_context.get('username') if user_context else None
                user_id_who_added = user_context.get('user_id') if user_context else None
                for hashtag in user_hashtags:
                    hashtag_query = """
                        INSERT INTO user_hashtags (tweet_id, hashtag, added_by, added_by_user_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """
                    cursor.execute(hashtag_query, (tweet_id, hashtag, user_who_added, user_id_who_added))
            
            # Insert scraped hashtags
            if scraped_hashtags:
                for hashtag in scraped_hashtags:
                    hashtag_query = """
                        INSERT INTO tweet_hashtags (tweet_id, hashtag)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    """
                    cursor.execute(hashtag_query, (tweet_id, hashtag))
            
            # Handle media files with download support
            if tweet_data.get('media'):
                self._save_media_files(cursor, tweet_data, tweet_id)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Tweet {tweet_data.get('id')} saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tweet {tweet_data.get('id')} to database: {e}")
            return False
    
    def _save_media_files(self, cursor, tweet_data: Dict[Any, Any], tweet_id: str):
        """Save media files with download metadata to database"""
        for media in tweet_data.get('media', []):
            # Extract download metadata if available
            local_path = media.get('local_path')
            hosted_url = media.get('hosted_url')
            file_size = media.get('file_size')
            download_status = 'success' if local_path else 'pending'
            
            media_query = """
                INSERT INTO media_files (
                    tweet_id, post_id, platform, media_type, original_url,
                    local_path, hosted_url, width, height, duration,
                    file_size, mime_type, download_status, downloaded_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tweet_id, original_url) DO UPDATE SET
                    local_path = EXCLUDED.local_path,
                    hosted_url = EXCLUDED.hosted_url,
                    file_size = EXCLUDED.file_size,
                    mime_type = EXCLUDED.mime_type,
                    download_status = EXCLUDED.download_status,
                    downloaded_at = EXCLUDED.downloaded_at;
            """
            
            cursor.execute(media_query, (
                tweet_id,  # tweet_id for backward compatibility
                tweet_id,  # post_id for new schema
                'twitter',
                media.get('type'),
                media.get('url'),
                local_path,
                hosted_url,
                media.get('width'),
                media.get('height'),
                media.get('duration'),
                file_size,
                media.get('mime_type'),
                download_status,
                datetime.now() if local_path else None
            ))
    
    async def download_media_for_tweet(self, tweet_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Download media files for a tweet and update the data"""
        if not self.download_media or not tweet_data.get('media'):
            return tweet_data
        
        try:
            tweet_id = str(tweet_data.get('id'))
            media_items = []
            
            # Convert tweet media to MediaItem objects
            from core.data_models import MediaItem, MediaType
            
            for media in tweet_data.get('media', []):
                media_type = MediaType.PHOTO
                if media.get('type') == 'video':
                    media_type = MediaType.VIDEO
                elif media.get('type') == 'animated_gif':
                    media_type = MediaType.ANIMATED_GIF
                
                media_item = MediaItem(
                    url=media.get('url'),
                    media_type=media_type,
                    width=media.get('width'),
                    height=media.get('height'),
                    duration=media.get('duration'),
                    mime_type=media.get('mime_type')
                )
                media_items.append(media_item)
            
            # Download media files
            media_metadata = await media_downloader.download_post_media(
                media_items, tweet_id, 'twitter'
            )
            
            # Update tweet_data with download information
            updated_media = []
            for i, original_media in enumerate(tweet_data.get('media', [])):
                updated_media_item = original_media.copy()
                
                if i < len(media_metadata):
                    metadata = media_metadata[i]
                    if metadata.get('status') == 'success':
                        updated_media_item['local_path'] = metadata.get('local_path')
                        updated_media_item['hosted_url'] = metadata.get('hosted_url')
                        updated_media_item['file_size'] = metadata.get('file_size')
                        if metadata.get('mime_type'):
                            updated_media_item['mime_type'] = metadata.get('mime_type')
                
                updated_media.append(updated_media_item)
            
            tweet_data['media'] = updated_media
            logger.info(f"Updated tweet {tweet_id} with media download info")
            
        except Exception as e:
            logger.error(f"Failed to download media for tweet {tweet_data.get('id')}: {e}")
        
        return tweet_data
    
    async def save_tweet_data(self, tweet_data: Dict[Any, Any], tweet_id: str, user_hashtags: List[str] = None, user_context: dict = None) -> List[str]:
        """Save tweet data with media downloading support"""
        # Download media files first
        if self.download_media:
            tweet_data = await self.download_media_for_tweet(tweet_data)
        
        filename = f"tweet_{tweet_id}.json"
        paths = self.get_storage_paths(filename)
        saved_paths = []
        
        # Add hashtags and user context to tweet data before saving to JSON
        enhanced_tweet_data = tweet_data.copy()
        if user_hashtags:
            enhanced_tweet_data['user_hashtags'] = user_hashtags
        
        # Add user context data for JSON storage
        if user_context:
            enhanced_tweet_data['user_context'] = {
                'telegram_user_id': user_context.get('user_id'),
                'telegram_username': user_context.get('username'),
                'added_notes': user_context.get('notes')
            }
        
        # Extract scraped hashtags from tweet text
        scraped_hashtags = []
        if 'text' in tweet_data:
            import re
            hashtag_pattern = r'#\w+'
            scraped_hashtags = re.findall(hashtag_pattern, tweet_data['text'])
        if scraped_hashtags:
            enhanced_tweet_data['scraped_hashtags'] = scraped_hashtags
        
        # Save to JSON files
        for path in paths:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Save the file with enhanced data
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_tweet_data, f, indent=2, ensure_ascii=False)
                
                saved_paths.append(path)
                logger.info(f"Tweet {tweet_id} saved to {path}")
                
            except Exception as e:
                logger.error(f"Failed to save tweet {tweet_id} to {path}: {e}")
        
        # Save to database
        if self.use_database:
            db_success = self.save_to_database(enhanced_tweet_data, user_hashtags, user_context)
            if db_success:
                saved_paths.append("PostgreSQL Database")
        
        return saved_paths
    
    def get_storage_info(self) -> str:
        """Get human-readable storage info"""
        info_parts = []
        
        if self.environment == 'local':
            info_parts.append(f"Local only ({self.local_path})")
        elif self.environment == 'server':
            info_parts.append(f"Server only ({self.server_path})")
        else:
            info_parts.append(f"Both local ({self.local_path}) and server ({self.server_path})")
        
        if self.use_database:
            info_parts.append("PostgreSQL Database")
        
        if self.download_media:
            info_parts.append("Media Download Enabled")
        
        return " + ".join(info_parts)

# Global instance
storage_manager = StorageManager()
