"""
Smart media downloader that uses enhanced downloader for platforms that need it
"""

import logging
from typing import List, Dict, Any

from .media_downloader import media_downloader
from .enhanced_media_downloader import enhanced_media_downloader
from .data_models import MediaItem, Platform

logger = logging.getLogger(__name__)

class SmartMediaDownloader:
    """
    Wrapper that routes to appropriate downloader based on platform and content
    """
    
    async def download_post_media(self, media_items: List[MediaItem], 
                                 post_id: str, 
                                 platform: str,
                                 raw_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Download media items, using enhanced downloader when needed
        
        Args:
            media_items: List of media items to download
            post_id: Post ID
            platform: Platform name
            raw_data: Raw post data (optional, used for Facebook stream detection)
            
        Returns:
            List of media metadata dictionaries
        """
        # Check if this is a Facebook video that needs merging
        if platform.lower() == 'facebook' and raw_data:
            needs_merge = raw_data.get('_needs_stream_merge', False)
            
            if needs_merge:
                logger.info(f"Using enhanced downloader for Facebook post {post_id} (stream merging needed)")
                return await enhanced_media_downloader.download_facebook_video(
                    raw_data, 
                    post_id
                )
        
        # For all other cases, use standard downloader
        return await media_downloader.download_post_media(
            media_items, 
            post_id, 
            platform
        )

# Global instance
smart_media_downloader = SmartMediaDownloader()
