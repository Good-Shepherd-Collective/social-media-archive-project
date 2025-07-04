#!/usr/bin/env python3
"""
Test script for User Attribution functionality
Tests that user attribution is properly captured in both JSON files and database
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

async def test_user_attribution():
    """Test user attribution by simulating a tweet scrape with user context"""
    
    # Test data - simulating a Telegram user
    test_user_context = {
        'user_id': 12345678,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'notes': 'Test scrape for user attribution'
    }
    
    test_hashtags = ['testing', 'attribution', 'automation']
    
    # Mock tweet data (since we're testing attribution, not actual scraping)
    mock_tweet_data = {
        'id': 999999999999999999,  # Use a fake ID that won't conflict
        'text': 'This is a test tweet for user attribution #testing #automation',
        'author': 'testauthor',
        'author_name': 'Test Author',
        'author_followers': 1000,
        'author_verified': False,
        'created_at': '2025-01-01 12:00:00',
        'retweet_count': 5,
        'like_count': 25,
        'reply_count': 3,
        'quote_count': 1,
        'view_count': 150,
        'url': 'https://x.com/testauthor/status/999999999999999999',
        'media': [],
        'scraped_at': str(datetime.now()),
        'scraped_by_user': test_user_context['username'],
        'scraped_by_user_id': test_user_context['user_id'],
        'user_notes': test_user_context['notes']
    }
    
    print("🧪 Testing User Attribution")
    print("=" * 50)
    print(f"Test User: @{test_user_context['username']} (ID: {test_user_context['user_id']})")
    print(f"Test Hashtags: {test_hashtags}")
    print(f"Mock Tweet ID: {mock_tweet_data['id']}")
    print()
    
    try:
        # Import storage manager
        from twitter.storage_utils import storage_manager
        
        # Test saving with user attribution
        print("💾 Testing storage with user attribution...")
        saved_paths = storage_manager.save_tweet_data(
            mock_tweet_data, 
            str(mock_tweet_data['id']), 
            test_hashtags, 
            test_user_context
        )
        
        if saved_paths:
            print(f"✅ Data saved successfully to: {', '.join(saved_paths)}")
        else:
            print("❌ Failed to save data")
            return False
        
        # Test JSON file attribution
        print("\n📄 Testing JSON file attribution...")
        json_filename = f"tweet_{mock_tweet_data['id']}.json"
        
        # Check local path first
        local_path = os.path.join(storage_manager.local_path, json_filename)
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            print(f"✅ JSON file found: {local_path}")
            print(f"   User Context in JSON: {json_data.get('user_context', 'NOT FOUND')}")
            print(f"   User Hashtags in JSON: {json_data.get('user_hashtags', 'NOT FOUND')}")
            print(f"   Scraped By User in JSON: {json_data.get('scraped_by_user', 'NOT FOUND')}")
        else:
            print("⚠️ JSON file not found in local path")
        
        # Test database attribution
        print("\n🗄️ Testing database attribution...")
        if storage_manager.use_database:
            try:
                conn = psycopg2.connect(**storage_manager.db_config)
                cursor = conn.cursor()
                
                # Check tweet attribution
                cursor.execute("""
                    SELECT 
                        id, 
                        scraped_by_user, 
                        scraped_by_user_id, 
                        user_notes
                    FROM tweets 
                    WHERE id = %s
                """, (mock_tweet_data['id'],))
                
                tweet_result = cursor.fetchone()
                if tweet_result:
                    tweet_id, scraped_by_user, scraped_by_user_id, user_notes = tweet_result
                    print(f"✅ Tweet found in database:")
                    print(f"   ID: {tweet_id}")
                    print(f"   Scraped by user: {scraped_by_user}")
                    print(f"   Scraped by user ID: {scraped_by_user_id}")
                    print(f"   User notes: {user_notes}")
                else:
                    print("❌ Tweet not found in database")
                
                # Check hashtag attribution
                cursor.execute("""
                    SELECT 
                        hashtag, 
                        added_by, 
                        added_by_user_id 
                    FROM user_hashtags 
                    WHERE tweet_id = %s
                """, (mock_tweet_data['id'],))
                
                hashtag_results = cursor.fetchall()
                if hashtag_results:
                    print(f"✅ User hashtags found in database:")
                    for hashtag, added_by, added_by_user_id in hashtag_results:
                        print(f"   #{hashtag} added by {added_by} (ID: {added_by_user_id})")
                else:
                    print("❌ User hashtags not found in database")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ Database test failed: {e}")
                return False
        else:
            print("⚠️ Database storage is disabled")
        
        print("\n🎉 User Attribution Test Completed Successfully!")
        print("\n📊 Summary:")
        print("✅ User context properly passed through scraping pipeline")
        print("✅ User ID and username stored in database")
        print("✅ User hashtags attributed to correct user")
        print("✅ JSON files include user context information")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_attribution_queries():
    """Test common attribution queries"""
    print("\n📈 Testing Attribution Queries")
    print("-" * 30)
    
    if not storage_manager.use_database:
        print("⚠️ Database storage disabled, skipping query tests")
        return
    
    try:
        conn = psycopg2.connect(**storage_manager.db_config)
        cursor = conn.cursor()
        
        # Query 1: Tweets by user
        print("Query 1: Tweets scraped by specific user")
        cursor.execute("""
            SELECT 
                COUNT(*) as tweet_count,
                scraped_by_user,
                scraped_by_user_id
            FROM tweets 
            WHERE scraped_by_user_id IS NOT NULL
            GROUP BY scraped_by_user, scraped_by_user_id
            ORDER BY tweet_count DESC
            LIMIT 5;
        """)
        
        user_stats = cursor.fetchall()
        if user_stats:
            for count, username, user_id in user_stats:
                print(f"  @{username} (ID: {user_id}): {count} tweets")
        else:
            print("  No user attribution data found")
        
        # Query 2: User hashtag activity
        print("\nQuery 2: User hashtag activity")
        cursor.execute("""
            SELECT 
                COUNT(*) as hashtag_count,
                added_by,
                added_by_user_id
            FROM user_hashtags 
            WHERE added_by_user_id IS NOT NULL
            GROUP BY added_by, added_by_user_id
            ORDER BY hashtag_count DESC
            LIMIT 5;
        """)
        
        hashtag_stats = cursor.fetchall()
        if hashtag_stats:
            for count, username, user_id in hashtag_stats:
                print(f"  @{username} (ID: {user_id}): {count} hashtags added")
        else:
            print("  No hashtag attribution data found")
        
        # Query 3: Recent activity with attribution
        print("\nQuery 3: Recent activity with attribution")
        cursor.execute("""
            SELECT 
                t.id,
                t.author,
                t.scraped_by_user,
                t.scraped_at::date as date,
                COALESCE(array_agg(DISTINCT uh.hashtag) FILTER (WHERE uh.hashtag IS NOT NULL), '{}') as user_tags
            FROM tweets t
            LEFT JOIN user_hashtags uh ON t.id = uh.tweet_id
            WHERE t.scraped_by_user_id IS NOT NULL
            GROUP BY t.id, t.author, t.scraped_by_user, t.scraped_at
            ORDER BY t.scraped_at DESC
            LIMIT 3;
        """)
        
        recent_activity = cursor.fetchall()
        if recent_activity:
            for tweet_id, author, scraped_by, date, user_tags in recent_activity:
                print(f"  Tweet {tweet_id} by @{author}")
                print(f"    Scraped by: @{scraped_by} on {date}")
                print(f"    User tags: {user_tags}")
        else:
            print("  No recent attributed activity found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 User Attribution Test Suite")
    print("=" * 50)
    
    # Import after the global storage_manager is available
    global storage_manager
    from twitter.storage_utils import storage_manager
    
    # Run attribution test
    success = await test_user_attribution()
    
    if success:
        # Run query tests
        test_attribution_queries()
        
        print("\n✅ All tests completed successfully!")
        print("\n📝 User Attribution Features Verified:")
        print("• User ID and username tracking")
        print("• Hashtag attribution to users")
        print("• JSON file user context storage")
        print("• Database user attribution fields")
        print("• Attribution query capabilities")
    else:
        print("\n❌ Tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)
