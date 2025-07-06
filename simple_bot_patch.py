#!/usr/bin/env python3
"""
Simple patch to handle Facebook video merging in the bot
"""

# Read the bot file
with open('/home/ubuntu/social-media-archive-project/main_bot.py', 'r') as f:
    lines = f.readlines()

# Find where media is downloaded and add a check for Facebook videos
inserted = False
for i, line in enumerate(lines):
    # Look for where we log "Downloaded media file"
    if 'logger.info(f"Downloaded media file: {local_filename}")' in line and not inserted:
        # Insert Facebook merge check after successful download
        indent = len(line) - len(line.lstrip())
        
        merge_code = f'''{' ' * indent}# Check if this is a Facebook video that needs audio merging
{' ' * indent}if (post_data.platform.value == 'facebook' and 
{' ' * indent}    media.media_type.value == 'video' and
{' ' * indent}    hasattr(post_data, 'raw_data') and 
{' ' * indent}    post_data.raw_data.get('_audio_stream')):
{' ' * indent}    
{' ' * indent}    # Download and merge audio
{' ' * indent}    audio_url = post_data.raw_data['_audio_stream'].get('base_url')
{' ' * indent}    if audio_url:
{' ' * indent}        logger.info(f"Downloading audio stream for Facebook video...")
{' ' * indent}        audio_path = local_path.parent / f"{{post_data.id}}_audio.mp4"
{' ' * indent}        merged_path = local_path.parent / f"{{post_data.id}}_merged.mp4"
{' ' * indent}        
{' ' * indent}        try:
{' ' * indent}            # Download audio
{' ' * indent}            audio_response = client.get(audio_url, timeout=30)
{' ' * indent}            if audio_response.status_code == 200:
{' ' * indent}                with open(audio_path, 'wb') as f:
{' ' * indent}                    f.write(audio_response.content)
{' ' * indent}                
{' ' * indent}                # Merge with ffmpeg
{' ' * indent}                import subprocess
{' ' * indent}                cmd = [
{' ' * indent}                    'ffmpeg', '-i', str(local_path), '-i', str(audio_path),
{' ' * indent}                    '-c:v', 'copy', '-c:a', 'copy', '-y', str(merged_path)
{' ' * indent}                ]
{' ' * indent}                result = subprocess.run(cmd, capture_output=True, text=True)
{' ' * indent}                
{' ' * indent}                if result.returncode == 0:
{' ' * indent}                    # Replace original with merged
{' ' * indent}                    import shutil
{' ' * indent}                    shutil.move(str(merged_path), str(local_path))
{' ' * indent}                    logger.info(f"Successfully merged video with audio")
{' ' * indent}                    downloaded_media[-1]['merged'] = True
{' ' * indent}                else:
{' ' * indent}                    logger.error(f"Failed to merge: {{result.stderr}}")
{' ' * indent}                
{' ' * indent}                # Clean up
{' ' * indent}                if audio_path.exists():
{' ' * indent}                    audio_path.unlink()
{' ' * indent}                if merged_path.exists():
{' ' * indent}                    merged_path.unlink()
{' ' * indent}                    
{' ' * indent}        except Exception as merge_error:
{' ' * indent}            logger.error(f"Failed to merge audio: {{merge_error}}")
{' ' * indent}
'''
        lines.insert(i + 1, merge_code)
        inserted = True
        print(f"Inserted merge code after line {i}")
        break

# Save the updated file
if inserted:
    with open('/home/ubuntu/social-media-archive-project/main_bot.py', 'w') as f:
        f.writelines(lines)
    print("Bot patched successfully!")
else:
    print("Could not find insertion point")
