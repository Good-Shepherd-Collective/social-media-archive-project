# This file contains the updated parse_media_items method for FacebookScraper

def parse_media_items(self, data: Dict[str, Any]) -> List[MediaItem]:
    """Parse media items from Facebook data"""
    media_items = []
    
    # Check post type
    post_type = data.get('type', '')
    
    if post_type in ["video_post", "reel"]:
        # Check for video_representations (the format from your example)
        if 'video_representations' in data:
            video_reps = data['video_representations']
            if video_reps:
                # Extract best video and audio streams
                video_streams = [r for r in video_reps if isinstance(r, dict) and r.get('height', 0) > 0]
                audio_streams = [r for r in video_reps if isinstance(r, dict) and r.get('height', 0) == 0 and 'mp4a' in r.get('codecs', '')]
                
                # Mark in raw_data if this needs merging
                data['_needs_stream_merge'] = bool(video_streams and audio_streams)
                
                if video_streams and audio_streams:
                    # We have separate streams - store both for merging
                    # Get best quality video
                    best_video = max(video_streams, key=lambda x: (x.get('height', 0), x.get('bandwidth', 0)))
                    audio_stream = audio_streams[0]  # Usually only one audio stream
                    
                    # Store stream info in raw data for downloader
                    data['_video_stream'] = best_video
                    data['_audio_stream'] = audio_stream
                    
                    # Create a placeholder media item that indicates merging needed
                    media_items.append(MediaItem(
                        url=best_video.get('base_url', ''),
                        media_type=MediaType.VIDEO,
                        width=best_video.get('width'),
                        height=best_video.get('height'),
                        duration=data.get('playable_duration_s'),
                        metadata={'needs_merge': True, 'has_audio': True}
                    ))
                elif video_streams:
                    # Only video (might have embedded audio)
                    best_video = max(video_streams, key=lambda x: (x.get('height', 0), x.get('bandwidth', 0)))
                    media_items.append(MediaItem(
                        url=best_video.get('base_url', ''),
                        media_type=MediaType.VIDEO,
                        width=best_video.get('width'),
                        height=best_video.get('height'),
                        duration=data.get('playable_duration_s')
                    ))
                    
        # Check for old format (representations)
        elif 'representations' in data and isinstance(data['representations'], dict):
            reps_data = data['representations'].get('representations', [])
            if reps_data:
                # Filter out audio-only and get best quality video
                video_reps = [r for r in reps_data if isinstance(r, dict) and r.get('height', 0) > 0]
                if video_reps:
                    best_video = max(video_reps, key=lambda x: x.get('bandwidth', 0))
                    media_items.append(MediaItem(
                        url=best_video.get('base_url', ''),
                        media_type=MediaType.VIDEO,
                        width=best_video.get('width'),
                        height=best_video.get('height'),
                        duration=data.get('length_in_second', data.get('playable_duration_s'))
                    ))
        
        # Add thumbnail
        if 'thumbnail_uri' in data:
            media_items.append(MediaItem(
                url=data['thumbnail_uri'],
                media_type=MediaType.PHOTO,
                metadata={'is_thumbnail': True}
            ))
    
    elif post_type == 'photo_post':
        # Handle photo posts
        if 'images' in data:
            for img in data['images']:
                media_items.append(MediaItem(
                    url=img.get('uri', ''),
                    media_type=MediaType.PHOTO,
                    width=img.get('width'),
                    height=img.get('height')
                ))
    
    # Handle regular posts that have an image field
    if 'image' in data and isinstance(data['image'], dict):
        img = data['image']
        if img.get('uri'):
            media_items.append(MediaItem(
                url=img.get('uri', ''),
                media_type=MediaType.PHOTO,
                width=img.get('width'),
                height=img.get('height')
            ))
    
    return media_items
