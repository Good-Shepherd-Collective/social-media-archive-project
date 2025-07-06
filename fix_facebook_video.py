#!/usr/bin/env python3
"""
Quick fix to download and merge Facebook video with audio
"""

import requests
import subprocess
from pathlib import Path

# The audio stream URL from the original data
audio_url = "https://video.fsgn13-2.fna.fbcdn.net/o1/v/t2/f2/m69/AQNB-O2LfF0M7njlYQ0U52x1_3maR2Prajh6skImMAa7swOvOog8hscpliqLXm9HQ3H07Sqs3RIWGz5JCjy8nTgC.mp4?strext=1&_nc_cat=106&_nc_oc=Adktolk_Kpf6OSpia6vmR_UkTYP3Hh9csrUGQMNG2QEbNXHNVsefvr9-jzkgpQ_GUxQ&_nc_sid=9ca052&_nc_ht=video.fsgn13-2.fna.fbcdn.net&_nc_ohc=fttw9vCAdVMQ7kNvwFdwMt2&efg=eyJ2ZW5jb2RlX3RhZyI6ImRhc2hfbG5faGVhYWNfdmJyM19hdWRpbyIsInZpZGVvX2lkIjo0MTI2MjQzMjcwOTM5NzQ0LCJvaWxfdXJsZ2VuX2FwcF9pZCI6MCwiY2xpZW50X25hbWUiOiJ1bmtub3duIiwieHB2X2Fzc2V0X2lkIjoxNjI0MjU3ODcxNzQ2NjgyLCJ2aV91c2VjYXNlX2lkIjoxMDEyMiwiZHVyYXRpb25fcyI6MjcsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&_nc_zt=28&oh=00_AfSkKy__3cc6ulv0nbtyyDjGa7CfXVQCiDNYCw95D5zs_A&oe=686F22C4"

video_path = Path("/home/ubuntu/social-media-archive-project/media_storage/data/media/4126243270939744_media_0.mp4")
audio_path = Path("/tmp/4126243270939744_audio.mp4")
output_path = Path("/home/ubuntu/social-media-archive-project/media_storage/data/media/4126243270939744_media_0_merged.mp4")

print("Downloading audio stream...")
try:
    response = requests.get(audio_url, timeout=30)
    if response.status_code == 200:
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        print(f"Audio downloaded: {audio_path.stat().st_size} bytes")
    else:
        print(f"Failed to download audio: HTTP {response.status_code}")
        exit(1)
except Exception as e:
    print(f"Error downloading audio: {e}")
    exit(1)

print("Merging video and audio...")
cmd = [
    'ffmpeg',
    '-i', str(video_path),
    '-i', str(audio_path),
    '-c:v', 'copy',
    '-c:a', 'copy',
    '-y',
    str(output_path)
]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print(f"Successfully merged! Output: {output_path}")
    print(f"Output size: {output_path.stat().st_size} bytes")
    
    # Replace the original with the merged version
    import shutil
    shutil.move(str(output_path), str(video_path))
    print(f"Replaced original video with merged version")
else:
    print(f"ffmpeg error: {result.stderr}")

# Clean up
if audio_path.exists():
    audio_path.unlink()
