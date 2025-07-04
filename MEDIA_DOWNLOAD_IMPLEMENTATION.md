# Media Download Implementation

## Overview

The social media archive project now includes comprehensive media downloading and self-hosting capabilities. When scraping tweets, the system automatically downloads all media files (images, videos, animated GIFs) and stores them locally while providing both original and self-hosted URLs.

## Features Implemented

### 1. Media Downloader (`core/media_downloader.py`)
- **Asynchronous downloading** using aiohttp for performance
- **Unique file naming** using content-based hashing to prevent duplicates
- **Directory organization** by media type (images, videos, audio, documents) and platform
- **Quality optimization** - downloads highest quality variants available
- **Error handling** with retry capabilities and status tracking
- **Storage statistics** and orphaned file cleanup

### 2. Enhanced Data Models (`core/data_models.py`)
- Extended `MediaItem` class with local storage fields:
  - `local_path`: Local filesystem path
  - `hosted_url`: Self-hosted URL for serving
  - `file_size`: Downloaded file size
  - `mime_type`: Content type

### 3. Updated Storage Managers
- **Unified Storage Manager** (`core/storage_manager.py`) - New modular system
- **Twitter Storage Utils** (`twitter/storage_utils.py`) - Backward compatible
- Both integrate media downloading into the save process

### 4. Database Schema Updates
- New columns in `media_files` table:
  - `local_path`: Path to downloaded file
  - `hosted_url`: URL to serve the file  
  - `download_status`: Status tracking (pending, success, failed)
  - `download_error`: Error message if download failed
  - `downloaded_at`: Timestamp of successful download

### 5. Media Server (`serve_media.py`)
- Simple HTTP server to serve downloaded media files
- CORS headers for web access
- Serves from `/home/ubuntu/social-media-archive-project/media_storage`
- Default port: 8000

## File Structure

```
media_storage/
├── images/
│   └── twitter/
│       ├── d0e0a2c7fe9b27ed.jpg
│       └── 25db32bc4a99643f.jpg
├── videos/
│   └── twitter/
└── audio/
    └── twitter/
```

## Configuration

### Environment Variables (.env)
```bash
# Media downloading configuration
DOWNLOAD_MEDIA=true
MEDIA_STORAGE_PATH=/home/ubuntu/social-media-archive-project/media_storage
MEDIA_BASE_URL=http://localhost:8000
```

### Dependencies Added
- `aiohttp>=3.8.0` - Async HTTP client for downloading
- `aiofiles>=23.0.0` - Async file operations

## Usage

### Automatic Media Download
When scraping tweets, media is automatically downloaded:

```python
# This now includes media downloading
tweet_data = await scrape_tweet_by_url(url, hashtags, user_context)
```

### Media Access
Each media item now contains both original and self-hosted URLs:

```json
{
  "url": "https://pbs.twimg.com/media/Gu_zmGrWYAAhGrk.jpg",
  "type": "photo", 
  "local_path": "/home/ubuntu/social-media-archive-project/media_storage/images/twitter/d0e0a2c7fe9b27ed.jpg",
  "hosted_url": "http://localhost:8000/images/twitter/d0e0a2c7fe9b27ed.jpg",
  "file_size": 84563,
  "mime_type": "image/jpeg"
}
```

### Starting the Media Server
```bash
python serve_media.py
```

## Testing

### Test Media Download
```bash
python test_media_download.py
```

### Test Complete Tweet Scraping
```bash
cd twitter
python scrape_tweet.py "https://x.com/yedidya_epstien/status/1941038199100293304" "test"
```

## Media Quality Optimization

### Twitter Images
- Automatically requests highest quality (`&name=orig`)
- Downloads original resolution when available

### Twitter Videos  
- Selects highest bitrate variant
- Prefers MP4 format for compatibility

### Twitter GIFs
- Downloads as MP4 format (Twitter's standard)
- Selects highest quality variant

## Database Integration

### Media Files Table
The system stores comprehensive metadata:
- Original URL and downloaded local path
- Download status and error tracking
- File metadata (size, dimensions, duration)
- Download timestamps

### Query Examples
```sql
-- Get all media for a tweet
SELECT * FROM media_files WHERE tweet_id = 1941038199100293304;

-- Get download statistics
SELECT 
  download_status, 
  COUNT(*) as count,
  SUM(file_size) as total_size
FROM media_files 
GROUP BY download_status;
```

## Benefits

1. **Permanence**: Media preserved even if original is deleted
2. **Performance**: Faster loading from local server
3. **Privacy**: No external requests when viewing archived content  
4. **Reliability**: Not dependent on external CDN availability
5. **Control**: Full control over media serving and access

## Current Status

✅ **Working Features:**
- Automatic media detection and downloading
- Local storage with organized directory structure
- Database integration with metadata
- Self-hosted serving via HTTP server
- Quality optimization for Twitter media
- Error handling and status tracking

🔄 **In Progress:**
- Database save error handling improvements
- Webhook bot integration testing

📋 **Future Enhancements:**
- Media server authentication
- CDN integration options
- Thumbnail generation
- Media transcoding capabilities
- Bulk download utilities

## Example Results

After scraping the test tweet with media:

**Original URL**: `https://pbs.twimg.com/media/Gu_zmGrWYAAhGrk.jpg`  
**Local Path**: `/home/ubuntu/social-media-archive-project/media_storage/images/twitter/d0e0a2c7fe9b27ed.jpg`  
**Hosted URL**: `http://localhost:8000/images/twitter/d0e0a2c7fe9b27ed.jpg`  
**File Size**: 84,563 bytes  

The system successfully provides both the original reference and a self-hosted alternative for permanent archival.
