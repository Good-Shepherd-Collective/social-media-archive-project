import json
from pathlib import Path
from datetime import datetime

def add_json_saving_to_webhook_bot():
    with open('webhook_bot.py', 'r') as f:
        content = f.read()
    
    # Add imports at the top
    import_addition = """import json
from pathlib import Path
from datetime import datetime"""
    
    if 'import json' not in content:
        content = content.replace('import asyncio', f'import asyncio\n{import_addition}')
    
    # Add save function
    save_function = '''
    def save_post_to_json(self, post_data, platform):
        """Save SocialMediaPost to JSON file"""
        try:
            # Create data directory if it doesn't exist
            data_dir = Path("/home/ubuntu/social-media-archive-project/media_storage/data")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert SocialMediaPost to dictionary
            post_dict = {
                'id': post_data.id,
                'platform': post_data.platform.value if hasattr(post_data.platform, 'value') else str(post_data.platform),
                'url': post_data.url,
                'text': post_data.text,
                'author': {
                    'username': post_data.author.username if post_data.author else None,
                    'display_name': post_data.author.display_name if post_data.author else None,
                    'followers_count': post_data.author.followers_count if post_data.author else 0,
                    'verified': post_data.author.verified if post_data.author else False,
                    'profile_url': post_data.author.profile_url if post_data.author else None,
                    'avatar_url': post_data.author.avatar_url if post_data.author else None
                },
                'created_at': post_data.created_at.isoformat() if post_data.created_at else None,
                'scraped_at': post_data.scraped_at.isoformat() if hasattr(post_data, 'scraped_at') and post_data.scraped_at else datetime.now().isoformat(),
                'metrics': {
                    'likes': post_data.metrics.likes if post_data.metrics else 0,
                    'shares': post_data.metrics.shares if post_data.metrics else 0,
                    'comments': post_data.metrics.comments if post_data.metrics else 0,
                    'views': post_data.metrics.views if post_data.metrics else None
                },
                'media': [
                    {
                        'url': media.url,
                        'type': media.media_type.value if hasattr(media.media_type, 'value') else str(media.media_type),
                        'width': media.width,
                        'height': media.height,
                        'mime_type': media.mime_type
                    } for media in post_data.media
                ] if post_data.media else [],
                'hashtags': post_data.scraped_hashtags if hasattr(post_data, 'scraped_hashtags') else []
            }
            
            # Save to JSON file
            filename = f"tweet_{post_data.id}.json" if platform.value == 'twitter' else f"{platform.value}_{post_data.id}.json"
            filepath = data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(post_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {platform.value} post {post_data.id} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save post to JSON: {e}")
            return False
'''
    
    # Add the save function to the class
    content = content.replace(
        'async def _send_success_response(self, update: Update, platform, post_data, user_hashtags: list, processing_msg):',
        save_function + '\n    async def _send_success_response(self, update: Update, platform, post_data, user_hashtags: list, processing_msg):'
    )
    
    # Add call to save function after successful scraping
    save_call = '''
                # Save post data to JSON file
                self.save_post_to_json(post_data, platform)
'''
    
    content = content.replace(
        '# Send success response with detailed format\n                await self._send_success_response(update, platform, post_data, user_hashtags, processing_msg)',
        f'{save_call}\n                # Send success response with detailed format\n                await self._send_success_response(update, platform, post_data, user_hashtags, processing_msg)'
    )
    
    with open('webhook_bot.py', 'w') as f:
        f.write(content)
    
    print("✅ Added JSON saving functionality to webhook bot")

if __name__ == '__main__':
    add_json_saving_to_webhook_bot()
