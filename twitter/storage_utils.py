"""
Storage utilities for Twitter scraper
Handles saving data to different locations based on environment
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'both')  # Default to 'both'
        self.local_path = os.getenv('LOCAL_STORAGE_PATH', '../scraped_data')
        self.server_path = os.getenv('SERVER_STORAGE_PATH', '/home/ubuntu/social-media-archive-project/scraped_data')
        
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
    
    def save_tweet_data(self, tweet_data: Dict[Any, Any], tweet_id: str) -> List[str]:
        """Save tweet data to appropriate location(s) based on environment"""
        filename = f"tweet_{tweet_id}.json"
        paths = self.get_storage_paths(filename)
        saved_paths = []
        
        for path in paths:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                # Save the file
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(tweet_data, f, indent=2, ensure_ascii=False)
                
                saved_paths.append(path)
                logger.info(f"Tweet {tweet_id} saved to {path}")
                
            except Exception as e:
                logger.error(f"Failed to save tweet {tweet_id} to {path}: {e}")
        
        return saved_paths
    
    def get_environment_info(self) -> str:
        """Get human-readable environment info"""
        if self.environment == 'local':
            return f"Local only ({self.local_path})"
        elif self.environment == 'server':
            return f"Server only ({self.server_path})"
        else:
            return f"Both local ({self.local_path}) and server ({self.server_path})"

# Global instance
storage_manager = StorageManager()
