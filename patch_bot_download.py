# This shows where to patch the bot to use smart downloader for Facebook videos

# In main_bot.py, around line 253-290, replace the media download logic with:

# Import at top of file:
from core.smart_media_downloader import smart_media_downloader
import asyncio

# In the save_json_data function, replace the media download section with:

if post_data.media:
    # Use smart downloader for platforms that need it
    if post_data.platform.value == 'facebook' and hasattr(post_data, 'raw_data'):
        # Use async smart downloader
        loop = asyncio.get_event_loop()
        media_metadata = loop.run_until_complete(
            smart_media_downloader.download_post_media(
                post_data.media,
                post_data.id,
                post_data.platform.value,
                post_data.raw_data
            )
        )
        
        # Convert metadata to bot's expected format
        for i, metadata in enumerate(media_metadata):
            if metadata.get('status') in ['success', 'already_exists']:
                local_path = metadata.get('local_path')
                if local_path:
                    # Copy to bot's media directory
                    import shutil
                    src_path = Path(local_path)
                    dst_filename = f"{post_data.id}_media_{i}.{src_path.suffix[1:]}"
                    dst_path = media_dir / dst_filename
                    
                    if not dst_path.exists():
                        shutil.copy2(src_path, dst_path)
                    
                    downloaded_media.append({
                        'url': post_data.media[i].url if i < len(post_data.media) else '',
                        'type': post_data.media[i].media_type.value if i < len(post_data.media) else 'unknown',
                        'width': post_data.media[i].width if i < len(post_data.media) else None,
                        'height': post_data.media[i].height if i < len(post_data.media) else None,
                        'mime_type': metadata.get('mime_type'),
                        'local_path': str(dst_path),
                        'hosted_url': f"https://ov-ab103a.infomaniak.ch/data/media/{dst_filename}",
                        'file_size': dst_path.stat().st_size if dst_path.exists() else None,
                        'merged': metadata.get('merged', False)
                    })
                    logger.info(f"Downloaded media file: {dst_filename}" + 
                              (" (merged)" if metadata.get('merged') else ""))
    else:
        # Use existing download logic for other platforms
        # ... existing code ...
