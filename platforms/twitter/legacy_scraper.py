"""
Twitter scraper with enhanced media downloading support
Updated to use the new media downloading system
"""

import asyncio
from datetime import datetime
from twscrape import API
from storage_utils import storage_manager
import logging

logger = logging.getLogger(__name__)

async def scrape_tweet_by_url(url: str, user_hashtags: list = None, user_context: dict = None):
    """
    Scrape a tweet by URL with media downloading support
    """
    api = API()
    
    # Extract tweet ID from URL
    tweet_id = int(url.split('/')[-1].split('?')[0])
    
    try:
        print(f"Scraping tweet ID: {tweet_id}")
        tweet = await api.tweet_details(tweet_id)
        
        if tweet:
            # Extract media if available
            media_data = []
            print(f"🔍 Checking for media in tweet...")
            print(f"   Tweet has 'media' attribute: {hasattr(tweet, 'media')}")
            
            if hasattr(tweet, 'media') and tweet.media:
                print(f"   tweet.media value: {tweet.media}")
                print(f"   tweet.media type: {type(tweet.media)}")
                
                if hasattr(tweet.media, 'photos'):
                    media_count = len(tweet.media.photos) + len(getattr(tweet.media, 'videos', [])) + len(getattr(tweet.media, 'animated', []))
                    print(f"   Found {media_count} total media items")
                    print(f"     Photos: {len(tweet.media.photos)}")
                    print(f"     Videos: {len(getattr(tweet.media, 'videos', []))}")
                    print(f"     Animated: {len(getattr(tweet.media, 'animated', []))}")
                
                # Process photos
                for i, media_item in enumerate(tweet.media.photos):
                    print(f"   Processing photo {i+1}...")
                    
                    # Get the best quality image URL
                    media_url = None
                    if hasattr(media_item, 'url'):
                        media_url = media_item.url
                        # Enhance URL to get highest quality
                        if '?format=' in media_url:
                            media_url = media_url.replace('&name=small', '&name=orig')
                            media_url = media_url.replace('&name=medium', '&name=orig')  
                            media_url = media_url.replace('&name=large', '&name=orig')
                    
                    if media_url:
                        media_data.append({
                            'url': media_url,
                            'type': 'photo',
                            'width': getattr(media_item, 'width', None),
                            'height': getattr(media_item, 'height', None),
                            'mime_type': 'image/jpeg'
                        })
                        print(f"     Added photo: {media_url}")
                
                # Process videos
                for i, media_item in enumerate(getattr(tweet.media, 'videos', [])):
                    print(f"   Processing video {i+1}...")
                    
                    # Get the best quality video URL
                    media_url = None
                    if hasattr(media_item, 'variants') and media_item.variants:
                        # Find best quality variant (highest bitrate)
                        video_variants = [v for v in media_item.variants 
                                        if getattr(v, 'contentType', '').startswith('video/')]
                        if video_variants:
                            best_variant = max(video_variants,
                                             key=lambda v: getattr(v, "bitrate", 0) if getattr(v, "bitrate", None) else 0)
                            media_url = getattr(best_variant, "url", None)
                    
                    if media_url:
                        media_data.append({
                            'url': media_url,
                            'type': 'video',
                            'width': getattr(media_item, 'width', None),
                            'height': getattr(media_item, 'height', None),
                            'duration': getattr(media_item, 'duration', None),
                            'mime_type': 'video/mp4'
                        })
                        print(f"     Added video: {media_url}")
                
                # Process animated GIFs
                for i, media_item in enumerate(getattr(tweet.media, 'animated', [])):
                    print(f"   Processing animated GIF {i+1}...")
                    
                    media_url = None
                    if hasattr(media_item, 'variants') and media_item.variants:
                        # For GIFs, prefer mp4 format
                        mp4_variants = [v for v in media_item.variants 
                                      if getattr(v, 'contentType', '') == 'video/mp4']
                        if mp4_variants:
                            best_variant = max(mp4_variants,
                                             key=lambda v: getattr(v, "bitrate", 0) if getattr(v, "bitrate", None) else 0)
                            media_url = getattr(best_variant, "url", None)
                        else:
                            # Fallback to any variant
                            media_url = getattr(media_item.variants[0], 'url', None) if media_item.variants else None
                    else:
                        media_url = getattr(media_item, 'url', None)
                    
                    if media_url:
                        media_data.append({
                            'url': media_url,
                            'type': 'animated_gif',
                            'width': getattr(media_item, 'width', None),
                            'height': getattr(media_item, 'height', None),
                            'mime_type': 'video/mp4'
                        })
                        print(f"     Added animated GIF: {media_url}")
            
            print(f"📊 Total media items extracted: {len(media_data)}")
            
            # Create tweet data structure
            tweet_data = {
                'id': tweet.id,
                'text': tweet.rawContent,
                'author': tweet.user.username,
                'author_name': tweet.user.displayname,
                'author_followers': tweet.user.followersCount,
                'author_verified': tweet.user.verified,
                'created_at': tweet.date.isoformat(),
                'retweet_count': tweet.retweetCount,
                'like_count': tweet.likeCount,
                'reply_count': tweet.replyCount,
                'quote_count': getattr(tweet, 'quoteCount', 0),
                'view_count': getattr(tweet, 'viewCount', None),
                'url': url,
                'media': media_data,
                'scraped_at': datetime.now().isoformat(),
                'scraped_by_user': user_context.get('username') if user_context else None,
                'scraped_by_user_id': user_context.get('user_id') if user_context else None,
                'user_notes': user_context.get('notes') if user_context else None
            }
            
            # Save tweet data with media downloading
            print(f"💾 Saving tweet data with media downloading...")
            saved_paths = await storage_manager.save_tweet_data(
                tweet_data, 
                str(tweet_id), 
                user_hashtags, 
                user_context
            )
            
            print(f"✅ Tweet saved to: {', '.join(saved_paths)}")
            
            # Log media download results
            if tweet_data.get('media'):
                print(f"📸 Media download results:")
                for i, media in enumerate(tweet_data.get('media', [])):
                    local_path = media.get('local_path')
                    hosted_url = media.get('hosted_url')
                    file_size = media.get('file_size')
                    
                    if local_path:
                        print(f"   Media {i+1}: ✅ Downloaded")
                        print(f"     Local: {local_path}")
                        print(f"     Hosted: {hosted_url}")
                        print(f"     Size: {file_size} bytes")
                    else:
                        print(f"   Media {i+1}: ❌ Download failed")
            
            return tweet_data
        else:
            print("❌ No tweet data returned")
            return None
            
    except Exception as e:
        print(f"❌ Error scraping tweet: {e}")
        logger.error(f"Error scraping tweet {tweet_id}: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        hashtags = sys.argv[2:] if len(sys.argv) > 2 else []
        asyncio.run(scrape_tweet_by_url(url, hashtags))
    else:
        print("Usage: python scrape_tweet.py <twitter_url> [hashtags...]")
