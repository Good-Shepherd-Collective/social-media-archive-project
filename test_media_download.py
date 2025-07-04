#!/usr/bin/env python3
"""
Test script for media downloading functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.media_downloader import media_downloader
from core.data_models import MediaItem, MediaType

async def test_media_download():
    """Test downloading a sample media file"""
    
    # Test with a sample Twitter media URL (using a placeholder)
    test_media = MediaItem(
        url="https://pbs.twimg.com/media/Gu_zmGrWYAAhGrk.jpg",  # From your example
        media_type=MediaType.PHOTO,
        mime_type="image/jpeg"
    )
    
    print("Testing media download functionality...")
    print(f"Media storage path: {media_downloader.base_path}")
    print(f"Media base URL: {media_downloader.base_url}")
    
    # Test download
    try:
        result = await media_downloader.download_media_item(
            test_media, 
            "test_post_123", 
            "twitter"
        )
        
        print(f"\nDownload result: {result}")
        
        if result.get('status') == 'success':
            local_path = result.get('local_path')
            hosted_url = result.get('hosted_url')
            file_size = result.get('file_size')
            
            print(f"✅ Successfully downloaded media!")
            print(f"📁 Local path: {local_path}")
            print(f"🌐 Hosted URL: {hosted_url}")
            print(f"📦 File size: {file_size} bytes")
            
            # Verify file exists
            if local_path and Path(local_path).exists():
                print(f"✅ File verified on disk: {Path(local_path).stat().st_size} bytes")
            else:
                print("❌ File not found on disk")
        else:
            print(f"❌ Download failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during download test: {e}")
    
    # Get storage stats
    try:
        stats = media_downloader.get_storage_stats()
        print(f"\n📊 Storage Statistics:")
        print(f"Total files: {stats['total_files']}")
        print(f"Total size: {stats['total_size']} bytes")
        for media_type, type_stats in stats['by_type'].items():
            print(f"  {media_type}: {type_stats['files']} files, {type_stats['size']} bytes")
    except Exception as e:
        print(f"❌ Error getting storage stats: {e}")

if __name__ == "__main__":
    asyncio.run(test_media_download())
