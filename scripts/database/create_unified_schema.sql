-- Unified Social Media Archive Database Schema
-- Supports Twitter, Instagram, TikTok, Facebook, and future platforms

-- Create the unified posts table if it doesn't exist
CREATE TABLE IF NOT EXISTS social_media_posts (
    id VARCHAR(255) PRIMARY KEY,
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('twitter', 'instagram', 'tiktok', 'facebook', 'other')),
    url TEXT NOT NULL,
    content TEXT,
    
    -- Author information
    author_username VARCHAR(255),
    author_display_name VARCHAR(255),
    author_id VARCHAR(255),
    author_followers INTEGER,
    author_verified BOOLEAN DEFAULT FALSE,
    author_profile_url TEXT,
    author_avatar_url TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Flexible metrics as JSONB
    metrics JSONB DEFAULT '{}',
    
    -- Media items as JSONB array
    media_items JSONB DEFAULT '[]',
    
    -- Hashtags
    scraped_hashtags TEXT[],
    user_hashtags TEXT[],
    
    -- User context
    telegram_user_id BIGINT,
    telegram_username VARCHAR(255),
    telegram_first_name VARCHAR(255),
    telegram_last_name VARCHAR(255),
    
    -- Full platform-specific data
    raw_data JSONB,
    
    -- Search
    search_vector tsvector,
    
    CONSTRAINT unique_platform_id UNIQUE (platform, id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_media_posts(platform);
CREATE INDEX IF NOT EXISTS idx_posts_author_username ON social_media_posts(author_username);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON social_media_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_scraped_at ON social_media_posts(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_telegram_user ON social_media_posts(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_posts_metrics ON social_media_posts USING GIN(metrics);
CREATE INDEX IF NOT EXISTS idx_posts_search ON social_media_posts USING GIN(search_vector);

-- Function to update search vector
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.author_username, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.author_display_name, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS update_posts_search_vector ON social_media_posts;
CREATE TRIGGER update_posts_search_vector
    BEFORE INSERT OR UPDATE ON social_media_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Create a view for backward compatibility with existing Twitter queries
CREATE OR REPLACE VIEW twitter_posts_view AS
SELECT 
    CASE 
        WHEN platform = 'twitter' AND id ~ '^\d+$' THEN id::BIGINT
        ELSE 0
    END as id,
    content as text,
    author_username as author,
    author_display_name as author_name,
    author_followers,
    author_verified,
    created_at,
    scraped_at,
    COALESCE((metrics->>'shares')::INTEGER, 0) as retweet_count,
    COALESCE((metrics->>'likes')::INTEGER, 0) as like_count,
    COALESCE((metrics->>'comments')::INTEGER, 0) as reply_count,
    COALESCE((metrics->>'views')::INTEGER, 0) as view_count,
    url as original_url,
    telegram_username as scraped_by_user,
    telegram_user_id as scraped_by_user_id,
    user_hashtags,
    scraped_hashtags,
    media_items as media,
    raw_data
FROM social_media_posts
WHERE platform = 'twitter';
