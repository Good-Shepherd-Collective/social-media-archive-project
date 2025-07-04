"""
Unified storage manager for all social media platforms
Enhanced with media downloading capabilities
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

from .data_models import SocialMediaPost, Platform, MediaType
from .exceptions import StorageError, DatabaseError
from .media_downloader import media_downloader

logger = logging.getLogger(__name__)

class UnifiedStorageManager:
    """Unified storage manager that handles all social media platforms"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'both')
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
    
    async def save_post(self, post: SocialMediaPost) -> List[str]:
        """
        Save a social media post to both JSON and database
        Now includes media downloading
        
        Args:
            post: The SocialMediaPost to save
            
        Returns:
            List of saved locations
            
        Raises:
            StorageError: If saving fails
        """
        try:
            saved_paths = []
            
            # Download media files if enabled
            if self.download_media and post.media:
                logger.info(f"Downloading {len(post.media)} media files for post {post.id}")
                media_metadata = await media_downloader.download_post_media(
                    post.media, post.id, post.platform.value
                )
                
                # Update post with downloaded media info
                self._update_post_with_media_metadata(post, media_metadata)
            
            # Save to JSON files
            json_paths = self._save_to_json(post)
            saved_paths.extend(json_paths)
            
            # Save to database
            if self.use_database:
                if await self._save_to_database(post):
                    saved_paths.append("PostgreSQL Database")
            
            logger.info(f"Successfully saved {post.platform.value} post {post.id} to: {', '.join(saved_paths)}")
            return saved_paths
            
        except Exception as e:
            logger.error(f"Failed to save {post.platform.value} post {post.id}: {e}")
            raise StorageError(f"Failed to save post: {str(e)}")
    
    def _update_post_with_media_metadata(self, post: SocialMediaPost, media_metadata: List[Dict[str, Any]]):
        """Update post media items with downloaded metadata"""
        for i, media_item in enumerate(post.media):
            if i < len(media_metadata):
                metadata = media_metadata[i]
                
                # Update media item with download info
                if metadata.get('status') == 'success':
                    media_item.local_path = metadata.get('local_path')
                    media_item.hosted_url = metadata.get('hosted_url')
                    media_item.file_size = metadata.get('file_size')
                    if metadata.get('mime_type'):
                        media_item.mime_type = metadata.get('mime_type')
                
                # Store download status in raw_data
                if not hasattr(media_item, 'download_metadata'):
                    media_item.download_metadata = {}
                media_item.download_metadata.update(metadata)
    
    def _save_to_json(self, post: SocialMediaPost) -> List[str]:
        """Save post to JSON files"""
        filename = post.get_filename()
        paths = self.get_storage_paths(filename)
        saved_paths = []
        
        # Convert post to dictionary
        post_data = post.to_dict()
        
        for path in paths:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Save the file
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(post_data, f, indent=2, ensure_ascii=False)
                
                saved_paths.append(path)
                logger.debug(f"Saved JSON to {path}")
                
            except Exception as e:
                logger.error(f"Failed to save JSON to {path}: {e}")
        
        return saved_paths
    
    async def _save_to_database(self, post: SocialMediaPost) -> bool:
        """Save post to PostgreSQL database"""
        if not self.use_database:
            return False
            
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Prepare data for insertion
            insert_data = {
                'id': post.id,
                'platform': post.platform.value,
                'text': post.text,
                'author': post.author.username,
                'author_name': post.author.display_name,
                'author_followers': post.author.followers_count,
                'author_verified': post.author.verified,
                'created_at': post.created_at,
                'scraped_at': post.scraped_at,
                'retweet_count': post.metrics.shares,  # Map shares to retweets for compatibility
                'like_count': post.metrics.likes,
                'reply_count': post.metrics.comments,
                'quote_count': 0,  # Platform-specific, will be overridden if available
                'view_count': post.metrics.views,
                'original_url': post.url,
                'scraped_by_user': post.user_context.telegram_username if post.user_context else None,
                'scraped_by_user_id': post.user_context.telegram_user_id if post.user_context else None,
                'user_notes': post.user_context.notes if post.user_context else None,
                'raw_data': Json(post.raw_data)
            }
            
            # Insert or update post (use tweets table for backward compatibility)
            insert_query = """
                INSERT INTO tweets (
                    id, text, author, author_name, author_followers, author_verified,
                    created_at, scraped_at, retweet_count, like_count, reply_count, 
                    quote_count, view_count, original_url, scraped_by_user,
                    scraped_by_user_id, user_notes, raw_data
                ) VALUES (
                    %(id)s, %(text)s, %(author)s, %(author_name)s, %(author_followers)s, %(author_verified)s,
                    %(created_at)s, %(scraped_at)s, %(retweet_count)s, %(like_count)s, %(reply_count)s,
                    %(quote_count)s, %(view_count)s, %(original_url)s, %(scraped_by_user)s,
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
                    scraped_by_user = EXCLUDED.scraped_by_user,
                    scraped_by_user_id = EXCLUDED.scraped_by_user_id,
                    user_notes = EXCLUDED.user_notes,
                    raw_data = EXCLUDED.raw_data;
            """
            
            cursor.execute(insert_query, insert_data)
            
            # Handle hashtags separately
            await self._save_hashtags(cursor, post)
            
            # Handle media files with download metadata
            await self._save_media_files(cursor, post)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"Saved {post.platform.value} post {post.id} to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {post.platform.value} post {post.id} to database: {e}")
            raise DatabaseError(f"Database save failed: {str(e)}")
    
    async def _save_hashtags(self, cursor, post: SocialMediaPost):
        """Save hashtags to database"""
        # Insert user hashtags
        if post.user_hashtags and post.user_context:
            for hashtag in post.user_hashtags:
                hashtag_query = """
                    INSERT INTO user_hashtags (tweet_id, hashtag, added_by, added_by_user_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """
                cursor.execute(hashtag_query, (
                    post.id,
                    hashtag,
                    post.user_context.telegram_username,
                    post.user_context.telegram_user_id
                ))
        
        # Insert scraped hashtags
        if post.scraped_hashtags:
            for hashtag in post.scraped_hashtags:
                hashtag_query = """
                    INSERT INTO tweet_hashtags (tweet_id, hashtag)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """
                cursor.execute(hashtag_query, (post.id, hashtag))
    
    async def _save_media_files(self, cursor, post: SocialMediaPost):
        """Save media files to database with download metadata"""
        if post.media:
            for media in post.media:
                # Get download metadata if available
                download_metadata = getattr(media, 'download_metadata', {})
                
                media_query = """
                    INSERT INTO media_files (
                        tweet_id, post_id, platform, media_type, original_url, 
                        local_path, hosted_url, width, height, duration, 
                        file_size, mime_type, download_status, download_error, downloaded_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id, original_url) DO UPDATE SET
                        local_path = EXCLUDED.local_path,
                        hosted_url = EXCLUDED.hosted_url,
                        file_size = EXCLUDED.file_size,
                        mime_type = EXCLUDED.mime_type,
                        download_status = EXCLUDED.download_status,
                        download_error = EXCLUDED.download_error,
                        downloaded_at = EXCLUDED.downloaded_at;
                """
                
                cursor.execute(media_query, (
                    post.id,  # tweet_id for backward compatibility
                    post.id,  # post_id for new schema
                    post.platform.value,
                    media.media_type.value,
                    media.url,
                    getattr(media, 'local_path', None),
                    getattr(media, 'hosted_url', None),
                    media.width,
                    media.height,
                    media.duration,
                    getattr(media, 'file_size', None),
                    media.mime_type,
                    download_metadata.get('status', 'pending'),
                    download_metadata.get('error', None),
                    download_metadata.get('downloaded_at', None)
                ))
    
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

# Global instance for backward compatibility
storage_manager = UnifiedStorageManager()
