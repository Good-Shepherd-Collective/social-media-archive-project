# Platform Data Differences Analysis

## Twitter/X
- **Unique metrics**: retweets, quote tweets, impressions/views
- **Unique features**: threads, quotes, mentions
- **Media**: Up to 4 images or 1 video per tweet
- **ID format**: Numeric string (snowflake ID)

## Instagram
- **Unique metrics**: saves, story views, reel plays
- **Unique features**: stories, reels, carousels, IGTV
- **Media**: Up to 10 images/videos in carousel, single video for reels
- **ID format**: Alphanumeric string

## TikTok
- **Unique metrics**: shares, downloads allowed
- **Unique features**: sounds/music, effects, duets, stitches
- **Media**: Single video with thumbnail
- **ID format**: Numeric string

## Facebook
- **Unique metrics**: reactions (like, love, wow, etc.), shares
- **Unique features**: albums, events, marketplace posts
- **Media**: Multiple images, videos, or mixed
- **ID format**: Numeric string with page/user prefix

## Proposed PostgreSQL Schema Strategy

### Option 1A: Single Table with JSONB (Recommended)
```sql
CREATE TABLE social_media_posts (
    -- Common fields
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    content TEXT,
    author_username VARCHAR(255),
    author_display_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    scraped_at TIMESTAMP WITH TIME ZONE,
    
    -- Flexible JSONB fields for platform differences
    metrics JSONB, -- {likes: 100, retweets: 50, saves: 10}
    media_items JSONB, -- [{url, type, thumbnail, duration}]
    platform_specific JSONB, -- {thread_id, reply_to, music_id, etc}
    
    -- User context
    telegram_user_id BIGINT,
    user_hashtags TEXT[]
);
```

### Option 1B: Single Table with Platform-Specific Columns
```sql
CREATE TABLE social_media_posts (
    -- Common fields (same as above)
    
    -- Twitter specific (NULL for other platforms)
    retweet_count INTEGER,
    quote_count INTEGER,
    
    -- Instagram specific
    saves_count INTEGER,
    is_reel BOOLEAN,
    
    -- TikTok specific
    music_id VARCHAR(255),
    music_title TEXT,
    
    -- Facebook specific
    reaction_counts JSONB
);
```

### Option 2: Inheritance with PostgreSQL Table Inheritance
```sql
-- Base table
CREATE TABLE social_media_posts (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    -- common fields
);

-- Platform-specific tables inherit from base
CREATE TABLE twitter_posts (
    retweet_count INTEGER,
    quote_count INTEGER
) INHERITS (social_media_posts);

CREATE TABLE instagram_posts (
    saves_count INTEGER,
    is_reel BOOLEAN
) INHERITS (social_media_posts);
```

## Recommendation: Option 1A with JSONB

This provides the best balance of:
1. **Flexibility**: Easy to add new platforms without schema changes
2. **Queryability**: PostgreSQL JSONB supports indexing and queries
3. **Simplicity**: Single table to maintain
4. **Performance**: JSONB indexes make queries fast

Example queries:
```sql
-- Find all posts with >1000 likes
SELECT * FROM social_media_posts 
WHERE (metrics->>'likes')::int > 1000;

-- Find Instagram reels
SELECT * FROM social_media_posts 
WHERE platform = 'instagram' 
AND platform_specific->>'post_type' = 'reel';

-- Find TikToks with specific music
SELECT * FROM social_media_posts 
WHERE platform = 'tiktok' 
AND platform_specific->>'music_id' = '123456';
```
