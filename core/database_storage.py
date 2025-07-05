"""
Database storage functionality for social media posts
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import Json
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from .data_models import SocialMediaPost

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseStorage:
    """Handles database storage for social media posts"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'social_media_archive'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def save_post(self, post: SocialMediaPost) -> bool:
        """Save a social media post to the database"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Prepare media items for JSON storage
            media_items = []
            for media in post.media:
                media_items.append({
                    'url': media.url,
                    'type': media.media_type.value,
                    'width': media.width,
                    'height': media.height,
                    'duration': media.duration,
                    'file_size': media.file_size,
                    'mime_type': media.mime_type,
                    'local_path': media.local_path,
                    'hosted_url': media.hosted_url
                })
            
            # Prepare metrics
            metrics = {
                'likes': post.metrics.likes,
                'shares': post.metrics.shares,
                'comments': post.metrics.comments,
                'views': post.metrics.views,
                'saves': post.metrics.saves
            }
            
            # Remove None values from metrics
            metrics = {k: v for k, v in metrics.items() if v is not None}
            
            # Insert or update the post
            cur.execute('''
                INSERT INTO social_media_posts (
                    id, platform, url, content,
                    author_username, author_display_name, author_id,
                    author_followers, author_verified, author_profile_url, author_avatar_url,
                    created_at, scraped_at,
                    metrics, media_items,
                    scraped_hashtags, user_hashtags,
                    telegram_user_id, telegram_username, telegram_first_name, telegram_last_name,
                    raw_data
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    scraped_at = EXCLUDED.scraped_at,
                    metrics = EXCLUDED.metrics,
                    media_items = EXCLUDED.media_items,
                    user_hashtags = EXCLUDED.user_hashtags,
                    raw_data = EXCLUDED.raw_data
            ''', (
                post.id,
                post.platform.value,
                post.url,
                post.text,
                post.author.username if post.author else None,
                post.author.display_name if post.author else None,
                getattr(post.author, 'id', None) if post.author else None,
                post.author.followers_count if post.author else None,
                post.author.verified if post.author else False,
                post.author.profile_url if post.author else None,
                post.author.avatar_url if post.author else None,
                post.created_at,
                post.scraped_at,
                Json(metrics),
                Json(media_items),
                post.scraped_hashtags,
                post.user_hashtags,
                post.user_context.telegram_user_id if post.user_context else None,
                post.user_context.telegram_username if post.user_context else None,
                post.user_context.first_name if post.user_context else None,
                post.user_context.last_name if post.user_context else None,
                Json(post.raw_data) if post.raw_data else None
            ))
            
            conn.commit()
            logger.info(f"Saved {post.platform.value} post {post.id} to database")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save post to database: {e}")
            return False
    
    def post_exists(self, post_id: str, platform: str) -> bool:
        """Check if a post already exists in the database"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            cur.execute('''
                SELECT EXISTS(
                    SELECT 1 FROM social_media_posts 
                    WHERE id = %s AND platform = %s
                )
            ''', (post_id, platform))
            
            exists = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            return exists
            
        except Exception as e:
            logger.error(f"Error checking if post exists: {e}")
            return False

# Global instance
database_storage = DatabaseStorage()
