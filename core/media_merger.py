"""
Media merger for combining video and audio streams
Used primarily for platforms that provide separate streams (e.g., Facebook)
"""

import os
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class MediaMerger:
    """Handles merging of separate video and audio streams"""
    
    def __init__(self):
        # Check if ffmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed and available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("ffmpeg not found - video/audio merging will not be available")
            return False
    
    def merge_video_audio(self, video_path: Path, audio_path: Path, 
                         output_path: Path) -> bool:
        """
        Merge video and audio files using ffmpeg
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for merged output file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.ffmpeg_available:
            logger.error("ffmpeg not available - cannot merge video and audio")
            return False
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', str(video_path),      # Input video
                '-i', str(audio_path),      # Input audio
                '-c:v', 'copy',             # Copy video codec (no re-encoding)
                '-c:a', 'copy',             # Copy audio codec (no re-encoding)
                '-y',                       # Overwrite output file
                str(output_path)
            ]
            
            logger.info(f"Merging video and audio: {video_path.name} + {audio_path.name} -> {output_path.name}")
            
            # Run ffmpeg
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode != 0:
                logger.error(f"ffmpeg merge failed: {result.stderr}")
                return False
            
            # Verify output file exists and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully merged to {output_path} ({output_path.stat().st_size} bytes)")
                return True
            else:
                logger.error("Merge produced empty or missing file")
                return False
                
        except Exception as e:
            logger.error(f"Error merging video/audio: {e}")
            return False
    
    def extract_best_streams(self, representations: list) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Extract best video and audio streams from Facebook representations
        
        Args:
            representations: List of stream representations from Facebook
            
        Returns:
            Tuple of (best_video_stream, audio_stream) or (None, None) if not found
        """
        video_streams = []
        audio_stream = None
        
        for rep in representations:
            if not isinstance(rep, dict):
                continue
                
            # Check if it's a video stream (has height > 0)
            height = rep.get('height', 0)
            if height > 0:
                video_streams.append(rep)
            # Check if it's an audio stream (height = 0 and has audio codec)
            elif height == 0 and 'mp4a' in rep.get('codecs', ''):
                audio_stream = rep
        
        # Get best quality video (highest bandwidth/resolution)
        best_video = None
        if video_streams:
            best_video = max(video_streams, 
                           key=lambda x: (x.get('height', 0), x.get('bandwidth', 0)))
        
        return best_video, audio_stream
    
    def needs_merging(self, media_data: Dict[str, Any]) -> bool:
        """
        Check if media data contains separate video and audio streams that need merging
        
        Args:
            media_data: Media data from platform (e.g., Facebook post data)
            
        Returns:
            bool: True if merging is needed
        """
        # Check for video_representations (new format)
        if 'video_representations' in media_data:
            reps = media_data.get('video_representations', [])
            if reps:
                # Check if we have both video and audio streams
                has_video = any(r.get('height', 0) > 0 for r in reps)
                has_audio = any(r.get('height', 0) == 0 and 'mp4a' in r.get('codecs', '') 
                              for r in reps)
                return has_video and has_audio
        
        return False

# Global instance
media_merger = MediaMerger()
