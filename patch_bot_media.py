#!/usr/bin/env python3
"""
Patch the bot to use smart media downloader for Facebook videos
"""

import re

# Read the original bot file
with open('/home/ubuntu/social-media-archive-project/main_bot.py', 'r') as f:
    content = f.read()

# Add import if not present
if 'from core.smart_media_downloader import smart_media_downloader' not in content:
    # Find the last import line
    last_import = max([m.end() for m in re.finditer(r'^from .+ import .+$', content, re.MULTILINE)])
    import_line = '\nfrom core.smart_media_downloader import smart_media_downloader'
    content = content[:last_import] + import_line + content[last_import:]
    print("Added smart_media_downloader import")

# Find the save_post_to_json function
save_json_match = re.search(r'def save_post_to_json.*?:\n', content)
if not save_json_match:
    print("Could not find save_post_to_json function")
    exit(1)

# Find the media download section
media_section_start = content.find("if post_data.media:", save_json_match.end())
if media_section_start == -1:
    print("Could not find media download section")
    exit(1)

# Find the end of the media download section (the except clause)
except_pos = content.find("except Exception as e:", media_section_start)
if except_pos == -1:
    except_pos = content.find("# Convert SocialMediaPost", media_section_start)

# Get the indentation level
line_start = content.rfind('\n', 0, media_section_start) + 1
base_indent = len(content[line_start:media_section_start])

# Create the new media download logic with proper indentation
new_logic = f'''if post_data.media:
{' ' * (base_indent + 4)}# Check if this is a Facebook video that needs merging
{' ' * (base_indent + 4)}if (post_data.platform.value == 'facebook' and 
{' ' * (base_indent + 8)}hasattr(post_data, 'raw_data') and 
{' ' * (base_indent + 8)}post_data.raw_data.get('_needs_stream_merge')):
{' ' * (base_indent + 8)}
{' ' * (base_indent + 8)}logger.info(f"Using smart downloader for Facebook post {{post_data.id}} (merging required)")
{' ' * (base_indent + 8)}
{' ' * (base_indent + 8)}# Use async smart downloader
{' ' * (base_indent + 8)}media_metadata = await smart_media_downloader.download_post_media(
{' ' * (base_indent + 12)}post_data.media,
{' ' * (base_indent + 12)}post_data.id,
{' ' * (base_indent + 12)}post_data.platform.value,
{' ' * (base_indent + 12)}post_data.raw_data
{' ' * (base_indent + 8)})
{' ' * (base_indent + 8)}
{' ' * (base_indent + 8)}# Process downloaded media
{' ' * (base_indent + 8)}for i, metadata in enumerate(media_metadata):
{' ' * (base_indent + 12)}if metadata.get('status') in ['success', 'already_exists']:
{' ' * (base_indent + 16)}src_path = metadata.get('local_path')
{' ' * (base_indent + 16)}if src_path:
{' ' * (base_indent + 20)}src_path = Path(src_path)
{' ' * (base_indent + 20)}file_extension = src_path.suffix[1:] if src_path.suffix else 'mp4'
{' ' * (base_indent + 20)}local_filename = f"{{post_data.id}}_media_{{i}}.{{file_extension}}"
{' ' * (base_indent + 20)}local_path = media_dir / local_filename
{' ' * (base_indent + 20)}
{' ' * (base_indent + 20)}# Copy to bot's media directory if needed
{' ' * (base_indent + 20)}if not local_path.exists() and src_path.exists():
{' ' * (base_indent + 24)}import shutil
{' ' * (base_indent + 24)}shutil.copy2(src_path, local_path)
{' ' * (base_indent + 20)}
{' ' * (base_indent + 20)}downloaded_media.append({{
{' ' * (base_indent + 24)}'url': post_data.media[i].url if i < len(post_data.media) else '',
{' ' * (base_indent + 24)}'type': post_data.media[i].media_type.value if i < len(post_data.media) else 'unknown',
{' ' * (base_indent + 24)}'width': post_data.media[i].width if i < len(post_data.media) else None,
{' ' * (base_indent + 24)}'height': post_data.media[i].height if i < len(post_data.media) else None,
{' ' * (base_indent + 24)}'mime_type': metadata.get('mime_type'),
{' ' * (base_indent + 24)}'local_path': str(local_path),
{' ' * (base_indent + 24)}'hosted_url': f"https://ov-ab103a.infomaniak.ch/data/media/{{local_filename}}",
{' ' * (base_indent + 24)}'file_size': local_path.stat().st_size if local_path.exists() else None,
{' ' * (base_indent + 24)}'merged': metadata.get('merged', False)
{' ' * (base_indent + 20)}}})
{' ' * (base_indent + 20)}logger.info(f"Downloaded media file: {{local_filename}}" + 
{' ' * (base_indent + 32)}(" (merged video+audio)" if metadata.get('merged') else ""))
{' ' * (base_indent + 16)}else:
{' ' * (base_indent + 20)}downloaded_media.append({{
{' ' * (base_indent + 24)}'url': post_data.media[i].url if i < len(post_data.media) else '',
{' ' * (base_indent + 24)}'type': post_data.media[i].media_type.value if i < len(post_data.media) else 'unknown',
{' ' * (base_indent + 24)}'local_path': None,
{' ' * (base_indent + 24)}'hosted_url': None,
{' ' * (base_indent + 24)}'download_error': metadata.get('error', 'Download failed')
{' ' * (base_indent + 20)}}})
{' ' * (base_indent + 12)}else:
{' ' * (base_indent + 16)}downloaded_media.append({{
{' ' * (base_indent + 20)}'url': post_data.media[i].url if i < len(post_data.media) else '',
{' ' * (base_indent + 20)}'type': post_data.media[i].media_type.value if i < len(post_data.media) else 'unknown',
{' ' * (base_indent + 20)}'local_path': None,
{' ' * (base_indent + 20)}'hosted_url': None,
{' ' * (base_indent + 20)}'download_error': metadata.get('error', 'Unknown error')
{' ' * (base_indent + 16)}}})
{' ' * (base_indent + 4)}else:
{' ' * (base_indent + 8)}# Original download logic for other platforms
{' ' * (base_indent + 8)}'''

# Replace the media section
content = content[:media_section_start] + new_logic + content[media_section_start + len("if post_data.media:"):]

# Save the patched file
with open('/home/ubuntu/social-media-archive-project/main_bot.py', 'w') as f:
    f.write(content)

print("Bot patched successfully!")
