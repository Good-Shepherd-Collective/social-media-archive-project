#!/usr/bin/env python3
"""
Test Facebook video/audio stream detection and merging
"""

import json
from core.media_merger import media_merger

# Sample data from the user
sample_data = {
    "post_id": "4126243270939744",
    "type": "video_post",
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
            "representation_id": "726692533441382v",
            "mime_type": "video/mp4",
            "codecs": "vp09.00.30.08.00.01.01.01.00",
            "base_url": "https://video.example.com/video_540p.mp4",
            "bandwidth": 2506222,
            "height": 960,
            "width": 540
        },
        {
            "representation_id": "2476696442692734v",
            "mime_type": "video/mp4",
            "codecs": "vp09.00.31.08.00.01.01.01.00",
            "base_url": "https://video.example.com/video_720p.mp4",
            "bandwidth": 4489498,
            "height": 1280,
            "width": 720
        },
        {
            "representation_id": "698250169873126v",
            "mime_type": "video/mp4",
            "codecs": "vp09.00.40.08.00.01.01.01.00",
            "base_url": "https://video.example.com/video_1080p.mp4",
            "bandwidth": 6019890,
            "height": 1920,
            "width": 1080
        },
        {
            "representation_id": "742484908195514a",
            "mime_type": "audio/mp4",
            "codecs": "mp4a.40.5",
            "base_url": "https://video.example.com/audio.mp4",
            "bandwidth": 39983,
            "height": 0,
            "width": 0
        }
    ]
}

print("Testing Facebook video/audio stream detection...")
print("=" * 60)

# Test if merging is needed
needs_merge = media_merger.needs_merging(sample_data)
print(f"Needs merging: {needs_merge}")

# Extract best streams
video_reps = sample_data.get('video_representations', [])
best_video, audio_stream = media_merger.extract_best_streams(video_reps)

print("\nBest video stream:")
if best_video:
    print(f"  - Resolution: {best_video['width']}x{best_video['height']}")
    print(f"  - Bandwidth: {best_video['bandwidth']}")
    print(f"  - Codec: {best_video['codecs']}")
else:
    print("  - Not found")

print("\nAudio stream:")
if audio_stream:
    print(f"  - Codec: {audio_stream['codecs']}")
    print(f"  - Bandwidth: {audio_stream['bandwidth']}")
else:
    print("  - Not found")

print("\nffmpeg available:", media_merger.ffmpeg_available)
