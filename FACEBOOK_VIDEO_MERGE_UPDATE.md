# Facebook Video/Audio Stream Merging Update

## What Was Changed

1. **Created `core/media_merger.py`**
   - Detects when Facebook videos have separate video and audio streams
   - Uses ffmpeg to merge streams together
   - Extracts best quality video stream and audio stream

2. **Created `core/enhanced_media_downloader.py`**
   - Extended media downloader that handles stream merging
   - Downloads video and audio separately then merges them
   - Falls back to regular download for videos with embedded audio

3. **Created `core/smart_media_downloader.py`**
   - Smart wrapper that routes to appropriate downloader
   - Uses enhanced downloader for Facebook videos that need merging
   - Uses regular downloader for everything else

4. **Updated `platforms/facebook/scraper.py`**
   - Now detects video_representations with separate streams
   - Marks posts that need stream merging in raw_data
   - Stores video and audio stream info for the downloader

5. **Updated `core/storage_manager.py`**
   - Now uses smart_media_downloader instead of media_downloader
   - Passes raw_data to downloader for stream detection

## Prerequisites

- ffmpeg must be installed: `sudo apt-get install ffmpeg`
- Already confirmed installed and working on your system

## How to Test

1. Cache has been cleared (Python __pycache__ files removed)
2. Bot process has been killed - restart it:
   ```bash
   cd /home/ubuntu/social-media-archive-project
   python main_bot.py
   ```

3. Test with a Facebook video URL that has separate streams
   - The example you provided would work perfectly
   - The bot should download both video and audio streams
   - Then merge them into a single file

## What to Expect

- For Facebook videos with separate streams:
  - Log messages will indicate "stream merging needed"
  - Two temporary files will be downloaded (video + audio)
  - ffmpeg will merge them into final video
  - Temporary files will be cleaned up
  - Final merged video will be stored

- For regular videos (with embedded audio):
  - Normal download process as before
  - No merging needed

## Verification

Check logs for messages like:
- "Using enhanced downloader for Facebook post XXX (stream merging needed)"
- "Downloading video stream for facebook post XXX"
- "Downloading audio stream for facebook post XXX"
- "Merging video and audio streams for facebook post XXX"
- "Successfully merged to /path/to/file.mp4"
