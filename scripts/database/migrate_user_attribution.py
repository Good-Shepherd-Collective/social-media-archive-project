#!/usr/bin/env python3
"""
Database Migration Script - Add User Attribution Fields
Adds scraped_by_user_id and added_by_user_id fields to support full user attribution
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Add user attribution fields to existing database"""
    try:
        # Connect to the social_media_archive database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432),
            database='social_media_archive'
        )
        cursor = conn.cursor()
        
        print("🔄 Running User Attribution Migration...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tweets' 
            AND column_name IN ('scraped_by_user_id');
        """)
        existing_tweet_columns = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_hashtags' 
            AND column_name IN ('added_by_user_id');
        """)
        existing_hashtag_columns = [row[0] for row in cursor.fetchall()]
        
        # Add scraped_by_user_id to tweets table if it doesn't exist
        if 'scraped_by_user_id' not in existing_tweet_columns:
            print("  Adding scraped_by_user_id column to tweets table...")
            cursor.execute("""
                ALTER TABLE tweets 
                ADD COLUMN scraped_by_user_id BIGINT;
            """)
            
            # Create index for the new column
            cursor.execute("""
                CREATE INDEX idx_tweets_scraped_by_user_id ON tweets(scraped_by_user_id);
            """)
            print("  ✅ Added scraped_by_user_id column and index")
        else:
            print("  ✅ scraped_by_user_id column already exists")
        
        # Add added_by_user_id to user_hashtags table if it doesn't exist
        if 'added_by_user_id' not in existing_hashtag_columns:
            print("  Adding added_by_user_id column to user_hashtags table...")
            cursor.execute("""
                ALTER TABLE user_hashtags 
                ADD COLUMN added_by_user_id BIGINT;
            """)
            print("  ✅ Added added_by_user_id column")
        else:
            print("  ✅ added_by_user_id column already exists")
        
        # Commit the changes
        conn.commit()
        
        # Verify the migration
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'tweets' 
            AND column_name LIKE '%user%'
            ORDER BY column_name;
        """)
        tweet_user_columns = cursor.fetchall()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'user_hashtags' 
            AND column_name LIKE '%user%'
            ORDER BY column_name;
        """)
        hashtag_user_columns = cursor.fetchall()
        
        print("\n📊 Migration Results:")
        print("  Tweets table user-related columns:")
        for col in tweet_user_columns:
            print(f"    - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        print("  User_hashtags table user-related columns:")
        for col in hashtag_user_columns:
            print(f"    - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 User Attribution Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_attribution():
    """Test that user attribution is working"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432),
            database='social_media_archive'
        )
        cursor = conn.cursor()
        
        print("\n🧪 Testing User Attribution...")
        
        # Test query to show tweets with user attribution
        cursor.execute("""
            SELECT 
                id,
                author,
                scraped_by_user,
                scraped_by_user_id,
                scraped_at
            FROM tweets 
            WHERE scraped_by_user IS NOT NULL 
            OR scraped_by_user_id IS NOT NULL
            ORDER BY scraped_at DESC
            LIMIT 5;
        """)
        
        results = cursor.fetchall()
        if results:
            print("  Recent tweets with user attribution:")
            for row in results:
                tweet_id, author, username, user_id, scraped_at = row
                print(f"    Tweet {tweet_id} by @{author}")
                print(f"      Scraped by: {username} (ID: {user_id}) at {scraped_at}")
        else:
            print("  No tweets with user attribution found (this is normal for new installations)")
        
        # Test query to show user hashtags with attribution
        cursor.execute("""
            SELECT 
                uh.hashtag,
                uh.added_by,
                uh.added_by_user_id,
                t.id as tweet_id,
                t.author
            FROM user_hashtags uh
            JOIN tweets t ON uh.tweet_id = t.id
            WHERE uh.added_by IS NOT NULL 
            OR uh.added_by_user_id IS NOT NULL
            ORDER BY uh.added_at DESC
            LIMIT 5;
        """)
        
        hashtag_results = cursor.fetchall()
        if hashtag_results:
            print("\n  Recent user hashtags with attribution:")
            for row in hashtag_results:
                hashtag, username, user_id, tweet_id, author = row
                print(f"    #{hashtag} added by {username} (ID: {user_id})")
                print(f"      On tweet {tweet_id} by @{author}")
        else:
            print("\n  No user hashtags with attribution found (this is normal for new installations)")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Attribution test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Attribution test failed: {e}")
        return False

def main():
    print("🚀 User Attribution Migration Script")
    print("=" * 50)
    
    # Check if PostgreSQL is accessible
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        sys.exit(1)
    
    # Run migration
    if not run_migration():
        sys.exit(1)
    
    # Test attribution
    if not test_attribution():
        print("⚠️ Migration completed but testing failed")
    
    print("\n📝 Next steps:")
    print("1. User attribution is now enabled")
    print("2. New tweets will track the Telegram user who scraped them")
    print("3. User hashtags will track who added them")
    print("4. Test by scraping a new tweet through the Telegram bot")

if __name__ == "__main__":
    main()
