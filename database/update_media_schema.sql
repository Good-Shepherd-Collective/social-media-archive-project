-- Update media_files table to include new fields for self-hosted media
-- This is an update script for existing installations

-- Add new columns if they don't exist
ALTER TABLE media_files 
ADD COLUMN IF NOT EXISTS post_id BIGINT,
ADD COLUMN IF NOT EXISTS platform VARCHAR(50),
ADD COLUMN IF NOT EXISTS hosted_url TEXT,
ADD COLUMN IF NOT EXISTS download_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS download_error TEXT,
ADD COLUMN IF NOT EXISTS duration INTEGER;

-- Update existing tweet_id references to work with new post_id system
-- This handles backward compatibility
UPDATE media_files 
SET post_id = tweet_id, platform = 'twitter' 
WHERE post_id IS NULL AND tweet_id IS NOT NULL;

-- Create new indexes for better performance
CREATE INDEX IF NOT EXISTS idx_media_post_platform ON media_files(post_id, platform);
CREATE INDEX IF NOT EXISTS idx_media_download_status ON media_files(download_status);
CREATE INDEX IF NOT EXISTS idx_media_hosted_url ON media_files(hosted_url);

-- Add foreign key constraint for new unified posts table (if it exists)
-- This will be used when we fully migrate to the unified schema
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'posts') THEN
        ALTER TABLE media_files 
        ADD CONSTRAINT fk_media_post 
        FOREIGN KEY (post_id, platform) 
        REFERENCES posts(id, platform) 
        ON DELETE CASCADE;
    END IF;
END $$;
