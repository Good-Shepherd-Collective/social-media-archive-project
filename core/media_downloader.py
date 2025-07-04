"""
Media downloader for social media archive project
Downloads and stores media files locally while preserving original URLs
"""

import os
import hashlib
import logging
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
from datetime import datetime
import mimetypes

from .data_models import MediaItem, MediaType
from .exceptions import MediaDownloadError

logger = logging.getLogger(__name__)

class MediaDownloader:
    """Downloads and manages media files from social media posts"""
    
    def __init__(self, base_path: str = None, base_url: str = None):
        self.base_path = Path(base_path or os.getenv('MEDIA_STORAGE_PATH', '/home/ubuntu/social-media-archive-project/media_storage'))
        self.base_url = base_url or os.getenv('MEDIA_BASE_URL', 'http://localhost:8000/media')
        
        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different media types
        for media_type in ['images', 'videos', 'audio', 'documents']:
            (self.base_path / media_type).mkdir(exist_ok=True)
    
    def _get_file_hash(self, url: str, additional_data: str = "") -> str:
        """Generate a unique hash for the file based on URL and additional data"""
        hash_input = f"{url}{additional_data}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()[:16]
    
    def _get_media_subdir(self, media_type: MediaType) -> str:
        """Get subdirectory name for media type"""
        if media_type in [MediaType.PHOTO, MediaType.ANIMATED_GIF]:
            return "images"
        elif media_type == MediaType.VIDEO:
            return "videos"
        elif media_type == MediaType.AUDIO:
            return "audio"
        else:
            return "documents"
    
    def _get_file_extension(self, url: str, content_type: str = None) -> str:
        """Get file extension from URL or content type"""
        # First try to get from URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and '.' in path:
            return Path(path).suffix.lower()
        
        # Try to get from content type
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            if extension:
                return extension.lower()
        
        # Default extensions based on common patterns
        if 'jpg' in url.lower() or 'jpeg' in url.lower():
            return '.jpg'
        elif 'png' in url.lower():
            return '.png'
        elif 'gif' in url.lower():
            return '.gif'
        elif 'mp4' in url.lower():
            return '.mp4'
        elif 'webm' in url.lower():
            return '.webm'
        
        return '.bin'  # Default fallback
    
    def _generate_local_path(self, media_item: MediaItem, post_id: str, platform: str) -> tuple[Path, str]:
        """Generate local file path and hosted URL"""
        # Create unique filename
        file_hash = self._get_file_hash(media_item.url, f"{post_id}_{platform}")
        subdir = self._get_media_subdir(media_item.media_type)
        
        # Create platform-specific subdirectory
        platform_dir = self.base_path / subdir / platform
        platform_dir.mkdir(exist_ok=True)
        
        # Generate filename with extension
        extension = self._get_file_extension(media_item.url, media_item.mime_type)
        filename = f"{file_hash}{extension}"
        local_path = platform_dir / filename
        
        # Generate hosted URL
        hosted_url = f"{self.base_url}/{subdir}/{platform}/{filename}"
        
        return local_path, hosted_url
    
    async def download_media_item(self, media_item: MediaItem, post_id: str, platform: str) -> Dict[str, Any]:
        """
        Download a single media item and return metadata
        
        Returns:
            dict: Contains local_path, hosted_url, file_size, mime_type, etc.
        """
        try:
            local_path, hosted_url = self._generate_local_path(media_item, post_id, platform)
            
            # Skip if file already exists
            if local_path.exists():
                file_size = local_path.stat().st_size
                logger.debug(f"Media file already exists: {local_path}")
                return {
                    'local_path': str(local_path),
                    'hosted_url': hosted_url,
                    'file_size': file_size,
                    'mime_type': media_item.mime_type,
                    'downloaded_at': datetime.now(),
                    'status': 'already_exists'
                }
            
            # Download the file
            async with aiohttp.ClientSession() as session:
                async with session.get(media_item.url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download media: HTTP {response.status} for {media_item.url}")
                        return {
                            'local_path': None,
                            'hosted_url': None,
                            'error': f"HTTP {response.status}",
                            'status': 'failed'
                        }
                    
                    # Get content type and size
                    content_type = response.headers.get('content-type', media_item.mime_type)
                    content_length = response.headers.get('content-length')
                    file_size = int(content_length) if content_length else None
                    
                    # Update mime_type if we got it from headers
                    if content_type and not media_item.mime_type:
                        media_item.mime_type = content_type
                    
                    # Write file to disk
                    async with aiofiles.open(local_path, 'wb') as f:
                        downloaded_size = 0
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded_size += len(chunk)
                    
                    # Get actual file size
                    actual_size = local_path.stat().st_size
                    
                    logger.info(f"Downloaded media: {media_item.url} -> {local_path} ({actual_size} bytes)")
                    
                    return {
                        'local_path': str(local_path),
                        'hosted_url': hosted_url,
                        'file_size': actual_size,
                        'mime_type': content_type or media_item.mime_type,
                        'downloaded_at': datetime.now(),
                        'status': 'success'
                    }
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading media: {media_item.url}")
            return {
                'local_path': None,
                'hosted_url': None,
                'error': 'timeout',
                'status': 'failed'
            }
        except Exception as e:
            logger.error(f"Error downloading media {media_item.url}: {e}")
            return {
                'local_path': None,
                'hosted_url': None,
                'error': str(e),
                'status': 'failed'
            }
    
    async def download_post_media(self, media_items: List[MediaItem], post_id: str, platform: str) -> List[Dict[str, Any]]:
        """
        Download all media items for a post
        
        Returns:
            List of media metadata dictionaries
        """
        if not media_items:
            return []
        
        logger.info(f"Downloading {len(media_items)} media items for {platform} post {post_id}")
        
        # Download all media items concurrently
        tasks = []
        for media_item in media_items:
            task = self.download_media_item(media_item, post_id, platform)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        media_metadata = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Exception downloading media item {i}: {result}")
                media_metadata.append({
                    'local_path': None,
                    'hosted_url': None,
                    'error': str(result),
                    'status': 'failed'
                })
            else:
                media_metadata.append(result)
        
        successful_downloads = sum(1 for r in media_metadata if r.get('status') == 'success')
        logger.info(f"Successfully downloaded {successful_downloads}/{len(media_items)} media items for post {post_id}")
        
        return media_metadata
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_type': {}
        }
        
        for media_type_dir in ['images', 'videos', 'audio', 'documents']:
            type_dir = self.base_path / media_type_dir
            if type_dir.exists():
                type_stats = {
                    'files': 0,
                    'size': 0
                }
                
                for file_path in type_dir.rglob('*'):
                    if file_path.is_file():
                        type_stats['files'] += 1
                        type_stats['size'] += file_path.stat().st_size
                
                stats['by_type'][media_type_dir] = type_stats
                stats['total_files'] += type_stats['files']
                stats['total_size'] += type_stats['size']
        
        return stats
    
    def cleanup_orphaned_files(self, valid_file_paths: List[str]) -> int:
        """Remove files that are no longer referenced in the database"""
        valid_paths = set(valid_file_paths)
        removed_count = 0
        
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file() and str(file_path) not in valid_paths:
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Removed orphaned file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned file {file_path}: {e}")
        
        return removed_count

# Global instance
media_downloader = MediaDownloader()
