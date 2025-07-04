-- Social Media Archive Database Schema
-- PostgreSQL with Full Text Search + User Hashtags

CREATE DATABASE social_media_archive;

-- Main tweets table
CREATE TABLE tweets (
    id BIGINT PRIMARY KEY,
    text TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_followers INTEGER,
    author_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Engagement metrics
    retweet_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    quote_count INTEGER DEFAULT 0,
    view_count INTEGER,
    
    -- URLs and references
    original_url TEXT NOT NULL,
    platform VARCHAR(50) DEFAULT 'twitter',
    
    -- User context
    scraped_by_user VARCHAR(255), -- Telegram username who scraped it
    scraped_by_user_id BIGINT, -- Telegram user ID who scraped it
    user_notes TEXT, -- Any additional notes from user
    
    -- Full JSON data for flexibility
    raw_data JSONB,
    
    -- Search vector for fast full-text search
    search_vector tsvector,
    
    CONSTRAINT tweets_id_unique UNIQUE (id)
);

-- User-provided hashtags (contextual tags added by users)
CREATE TABLE user_hashtags (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    hashtag VARCHAR(255) NOT NULL,
    added_by VARCHAR(255), -- Telegram username who added it
    added_by_user_id BIGINT, -- Telegram user ID who added it
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Original hashtags from the tweet content
CREATE TABLE tweet_hashtags (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    hashtag VARCHAR(255) NOT NULL
);

-- Media files table
CREATE TABLE media_files (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    media_type VARCHAR(50) NOT NULL, -- 'image', 'video', 'gif'
    original_url TEXT NOT NULL,
    local_path TEXT, -- Path to downloaded file
    hosted_url TEXT, -- URL to serve the file
    file_size BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    downloaded_at TIMESTAMP WITH TIME ZONE
);

-- User mentions from tweet
CREATE TABLE mentions (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL
);

-- Create indexes for performance
CREATE INDEX idx_tweets_author ON tweets(author);
CREATE INDEX idx_tweets_created_at ON tweets(created_at DESC);
CREATE INDEX idx_tweets_like_count ON tweets(like_count DESC);
CREATE INDEX idx_tweets_retweet_count ON tweets(retweet_count DESC);
CREATE INDEX idx_tweets_scraped_by_user ON tweets(scraped_by_user);
CREATE INDEX idx_tweets_scraped_by_user_id ON tweets(scraped_by_user_id);

-- Index for hashtags
CREATE INDEX idx_user_hashtags_tweet_id ON user_hashtags(tweet_id);
CREATE INDEX idx_user_hashtags_hashtag ON user_hashtags(hashtag);
CREATE INDEX idx_tweet_hashtags_tweet_id ON tweet_hashtags(tweet_id);
CREATE INDEX idx_tweet_hashtags_hashtag ON tweet_hashtags(hashtag);

-- Index for media
CREATE INDEX idx_media_tweet_id ON media_files(tweet_id);
CREATE INDEX idx_media_type ON media_files(media_type);

-- GIN index for full-text search (most important!)
CREATE INDEX idx_tweets_search_vector ON tweets USING GIN(search_vector);

-- GIN index for JSON queries
CREATE INDEX idx_tweets_raw_data ON tweets USING GIN(raw_data);

-- Function to update search vector automatically
-- Includes user hashtags and notes in search
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
DECLARE
    user_tags TEXT := '';
    tweet_tags TEXT := '';
BEGIN
    -- Get user hashtags for this tweet
    SELECT string_agg(hashtag, ' ') INTO user_tags
    FROM user_hashtags 
    WHERE tweet_id = NEW.id;
    
    -- Get original tweet hashtags
    SELECT string_agg(hashtag, ' ') INTO tweet_tags
    FROM tweet_hashtags 
    WHERE tweet_id = NEW.id;
    
    -- Build search vector with weighted content
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.text, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.author, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.author_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.user_notes, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(user_tags, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(tweet_tags, '')), 'B');
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update search vector
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON tweets
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Function to refresh search vector when hashtags are added
CREATE OR REPLACE FUNCTION refresh_tweet_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the search vector for the tweet when hashtags change
    UPDATE tweets SET scraped_at = scraped_at WHERE id = COALESCE(NEW.tweet_id, OLD.tweet_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Triggers to refresh search when hashtags are modified
CREATE TRIGGER trigger_user_hashtags_search_refresh
    AFTER INSERT OR UPDATE OR DELETE ON user_hashtags
    FOR EACH ROW
    EXECUTE FUNCTION refresh_tweet_search_vector();

CREATE TRIGGER trigger_tweet_hashtags_search_refresh
    AFTER INSERT OR UPDATE OR DELETE ON tweet_hashtags
    FOR EACH ROW
    EXECUTE FUNCTION refresh_tweet_search_vector();

-- Views for easier querying

-- Combined hashtags view
CREATE VIEW tweet_all_hashtags AS
SELECT 
    tweet_id,
    hashtag,
    'user' as hashtag_source,
    added_by as source_user,
    added_at as created_at
FROM user_hashtags
UNION ALL
SELECT 
    tweet_id,
    hashtag,
    'tweet' as hashtag_source,
    NULL as source_user,
    NULL as created_at
FROM tweet_hashtags;

-- Rich tweet view with all data
CREATE VIEW tweets_enriched AS
SELECT 
    t.*,
    COALESCE(
        array_agg(DISTINCT uh.hashtag) FILTER (WHERE uh.hashtag IS NOT NULL), 
        '{}'
    ) as user_hashtags,
    COALESCE(
        array_agg(DISTINCT th.hashtag) FILTER (WHERE th.hashtag IS NOT NULL), 
        '{}'
    ) as tweet_hashtags,
    COALESCE(
        array_agg(DISTINCT m.hosted_url) FILTER (WHERE m.hosted_url IS NOT NULL), 
        '{}'
    ) as media_urls
FROM tweets t
LEFT JOIN user_hashtags uh ON t.id = uh.tweet_id
LEFT JOIN tweet_hashtags th ON t.id = th.tweet_id  
LEFT JOIN media_files m ON t.id = m.tweet_id
GROUP BY t.id;
