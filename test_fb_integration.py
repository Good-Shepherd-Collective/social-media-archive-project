#!/usr/bin/env python3
"""
Test Facebook video/audio merging integration
"""

import asyncio
import json
from datetime import datetime

from platforms.facebook.scraper import FacebookScraper
from core.data_models import MediaType

# Test data that mimics the user's example
test_data = {
    "post_id": "4126243270939744",
    "type": "video_post",
    "url": "https://www.facebook.com/gazaesncm/videos/4126243270939744/",
    "message": "فيديو من جلسات تعليم العود في المحافظة الوسطى بقطاع غزة",
    "timestamp": 1751539667,
    "author": {
        "id": "100057687211666",
        "name": "The Edward Said National Conservatory of Music - GAZA Branch",
        "url": "https://www.facebook.com/gazaesncm"
    },
    "video_representations": [
        {
            "representation_id": "1816575459240349v",
            "mime_type": "video/mp4",
            "codecs": "vp09.00.21.08.00.01.01.01.00",
            "base_url": "https://video.example.com/video_360p.mp4",
            "bandwidth": 835751,
            "height": 640,
            "width": 360
        },
        {
            "representation_id": "742484908195514a",
            "mime_type": "audio/mp4",
            "codecs": "mp4a.40.5",
            "base_url": "https://audio.example.com/audio.mp4",
            "bandwidth": 39983,
            "height": 0,
            "width": 0
        }
    ],
    "thumbnail_uri": "https://example.com/thumbnail.jpg",
    "playable_duration_s": 27,
    "reactions_count": 273,
    "comments_count": 23
}

async def test_facebook_parsing():
    """Test Facebook scraper parsing with stream detection"""
    print("Testing Facebook scraper with video/audio streams...")
    print("=" * 60)
    
    scraper = FacebookScraper()
    
    # Parse the test data
    post = scraper.parse_facebook_data(test_data, test_data['url'], None)
    
    print(f"Post ID: {post.id}")
    print(f"Platform: {post.platform.value}")
    print(f"Media items: {len(post.media)}")
    
    for i, media in enumerate(post.media):
        print(f"\nMedia item {i+1}:")
        print(f"  Type: {media.media_type.value}")
        print(f"  URL: {media.url[:50]}...")
        if media.width and media.height:
            print(f"  Resolution: {media.width}x{media.height}")
        if media.duration:
            print(f"  Duration: {media.duration}s")
    
    # Check raw data for merge flag
    print(f"\nNeeds stream merge: {post.raw_data.get('_needs_stream_merge', False)}")
    
    if '_video_stream' in post.raw_data:
        print(f"Video stream stored: {post.raw_data['_video_stream']['height']}p")
    if '_audio_stream' in post.raw_data:
        print(f"Audio stream stored: Yes")

if __name__ == "__main__":
    asyncio.run(test_facebook_parsing())
