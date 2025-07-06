"""
Enhanced media downloader with video/audio merging support
"""

import os
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from .media_downloader import MediaDownloader
from .media_merger import media_merger
from .data_models import MediaItem, MediaType
from .exceptions import MediaDownloadError

logger = logging.getLogger(__name__)

class EnhancedMediaDownloader(MediaDownloader):
    """Extended media downloader with stream merging capabilities"""
    
    async def download_and_merge_streams(self, video_stream: Dict[str, Any], 
                                       audio_stream: Dict[str, Any],
                                       post_id: str, 
                                       platform: str) -> Dict[str, Any]:
        """
        Download video and audio streams separately and merge them
        
        Args:
            video_stream: Video stream data with 'base_url', 'width', 'height', etc.
            audio_stream: Audio stream data with 'base_url'
            post_id: Post ID for filename generation
            platform: Platform name
            
        Returns:
            dict: Metadata about the merged file
        """
        try:
            # Create temporary directory for intermediate files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create MediaItem objects for video and audio
                video_item = MediaItem(
                    url=video_stream['base_url'],
                    media_type=MediaType.VIDEO,
                    width=video_stream.get('width'),
                    height=video_stream.get('height'),
                    mime_type='video/mp4'
                )
                
                audio_item = MediaItem(
                    url=audio_stream['base_url'],
                    media_type=MediaType.AUDIO,
                    mime_type='audio/mp4'
                )
                
                # Download video stream
                logger.info(f"Downloading video stream for {platform} post {post_id}")
                video_result = await self.download_media_item(
                    video_item, 
                    f"{post_id}_video", 
                    platform
                )
                
                if video_result['status'] != 'success' and video_result['status'] != 'already_exists':
                    logger.error(f"Failed to download video stream: {video_result.get('error')}")
                    return video_result
                
                # Download audio stream
                logger.info(f"Downloading audio stream for {platform} post {post_id}")
                audio_result = await self.download_media_item(
                    audio_item, 
                    f"{post_id}_audio", 
                    platform
                )
                
                if audio_result['status'] != 'success' and audio_result['status'] != 'already_exists':
                    logger.error(f"Failed to download audio stream: {audio_result.get('error')}")
                    return audio_result
                
                # Paths to downloaded files
                video_path = Path(video_result['local_path'])
                audio_path = Path(audio_result['local_path'])
                
                # Generate final output path
                final_item = MediaItem(
                    url=video_stream['base_url'],  # Use video URL as primary
                    media_type=MediaType.VIDEO,
                    width=video_stream.get('width'),
                    height=video_stream.get('height'),
                    mime_type='video/mp4'
                )
                
                final_path, hosted_url = self._generate_local_path(
                    final_item, 
                    post_id, 
                    platform
                )
                
                # Check if merged file already exists
                if final_path.exists():
                    logger.info(f"Merged file already exists: {final_path}")
                    # Clean up intermediate files if they're not the final file
                    if str(video_path) != str(final_path):
                        try:
                            video_path.unlink()
                            audio_path.unlink()
                        except:
                            pass
                    
                    return {
                        'local_path': str(final_path),
                        'hosted_url': hosted_url,
                        'file_size': final_path.stat().st_size,
                        'mime_type': 'video/mp4',
                        'status': 'already_exists',
                        'merged': True
                    }
                
                # Merge video and audio
                logger.info(f"Merging video and audio streams for {platform} post {post_id}")
                merge_success = media_merger.merge_video_audio(
                    video_path, 
                    audio_path, 
                    final_path
                )
                
                if not merge_success:
                    logger.error("Failed to merge video and audio streams")
                    # Clean up intermediate files
                    try:
                        if str(video_path) != str(final_path):
                            video_path.unlink()
                            audio_path.unlink()
                    except:
                        pass
                    
                    return {
                        'local_path': None,
                        'hosted_url': None,
                        'error': 'merge_failed',
                        'status': 'failed'
                    }
                
                # Clean up intermediate files
                try:
                    if str(video_path) != str(final_path):
                        video_path.unlink()
                        audio_path.unlink()
                    logger.info("Cleaned up intermediate stream files")
                except Exception as e:
                    logger.warning(f"Failed to clean up intermediate files: {e}")
                
                # Return merged file metadata
                return {
                    'local_path': str(final_path),
                    'hosted_url': hosted_url,
                    'file_size': final_path.stat().st_size,
                    'mime_type': 'video/mp4',
                    'status': 'success',
                    'merged': True
                }
                
        except Exception as e:
            logger.error(f"Error in download_and_merge_streams: {e}")
            return {
                'local_path': None,
                'hosted_url': None,
                'error': str(e),
                'status': 'failed'
            }
    
    async def download_facebook_video(self, media_data: Dict[str, Any], 
                                    post_id: str) -> List[Dict[str, Any]]:
        """
        Special handler for Facebook videos that may have separate streams
        
        Args:
            media_data: Facebook post data containing video_representations
            post_id: Post ID
            
        Returns:
            List of media metadata dictionaries
        """
        results = []
        
        # Check if we have video_representations
        video_reps = media_data.get('video_representations', [])
        if not video_reps:
            logger.warning("No video representations found in Facebook data")
            return results
        
        # Extract best video and audio streams
        best_video, audio_stream = media_merger.extract_best_streams(video_reps)
        
        if best_video and audio_stream:
            # We have separate streams - download and merge
            logger.info(f"Found separate video ({best_video.get('height')}p) and audio streams for Facebook post {post_id}")
            
            merge_result = await self.download_and_merge_streams(
                best_video,
                audio_stream,
                post_id,
                'facebook'
            )
            results.append(merge_result)
            
        elif best_video:
            # Only video stream (might have embedded audio)
            logger.info(f"Found single video stream ({best_video.get('height')}p) for Facebook post {post_id}")
            
            video_item = MediaItem(
                url=best_video['base_url'],
                media_type=MediaType.VIDEO,
                width=best_video.get('width'),
                height=best_video.get('height'),
                mime_type='video/mp4'
            )
            
            video_result = await self.download_media_item(
                video_item,
                post_id,
                'facebook'
            )
            results.append(video_result)
        
        # Also download thumbnail if available
        if 'thumbnail_uri' in media_data:
            logger.info(f"Downloading thumbnail for Facebook post {post_id}")
            thumb_item = MediaItem(
                url=media_data['thumbnail_uri'],
                media_type=MediaType.PHOTO,
                mime_type='image/jpeg'
            )
            
            thumb_result = await self.download_media_item(
                thumb_item,
                f"{post_id}_thumb",
                'facebook'
            )
            results.append(thumb_result)
        
        return results

# Create enhanced downloader instance
enhanced_media_downloader = EnhancedMediaDownloader()
