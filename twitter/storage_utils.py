"""
Storage utilities for Twitter scraper
Handles saving data to different locations based on environment
Enhanced with PostgreSQL database support
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'both')  # Default to 'both'
        self.local_path = os.getenv('LOCAL_STORAGE_PATH', '../scraped_data')
        self.server_path = os.getenv('SERVER_STORAGE_PATH', '/home/ubuntu/social-media-archive-project/scraped_data')
        
        # Database configuration
        self.use_database = os.getenv('USE_DATABASE', 'true').lower() == 'true'
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
        """Save tweet data to PostgreSQL database"""
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
            
            # Insert media files
            if tweet_data.get('media'):
                for media in tweet_data.get('media', []):
                    media_query = """
                        INSERT INTO media_files (tweet_id, media_type, original_url, width, height)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """
                    cursor.execute(media_query, (
                        tweet_id,
                        media.get('type'),
                        media.get('url'),
                        media.get('width'),
                        media.get('height')
                    ))
            
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Tweet {tweet_data.get('id')} saved to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save tweet {tweet_data.get('id')} to database: {e}")
            return False
    
    def save_tweet_data(self, tweet_data: Dict[Any, Any], tweet_id: str, user_hashtags: List[str] = None, user_context: dict = None) -> List[str]:
        """Save tweet data to appropriate location(s) based on environment"""
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
            db_success = self.save_to_database(tweet_data, user_hashtags, user_context)
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
        
        return " + ".join(info_parts)

# Global instance
storage_manager = StorageManager()
