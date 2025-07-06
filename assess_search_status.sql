-- PostgreSQL Search Assessment Script
-- Run this to understand current search capabilities

\echo '====================================='
\echo 'PostgreSQL Full-Text Search Assessment'
\echo '====================================='
\echo ''

-- Check PostgreSQL version
\echo 'PostgreSQL Version:'
SELECT version();
\echo ''

-- Check installed extensions
\echo 'Installed Extensions:'
SELECT name, version FROM pg_available_extensions 
WHERE installed_version IS NOT NULL 
AND name IN ('pg_trgm', 'unaccent', 'fuzzystrmatch');
\echo ''

-- Analyze search vector quality
\echo 'Search Vector Analysis:'
SELECT 
    COUNT(*) as total_posts,
    COUNT(search_vector) as posts_with_vector,
    COUNT(*) FILTER (WHERE length(search_vector::text) > 10) as populated_vectors,
    COUNT(*) FILTER (WHERE search_vector IS NULL) as null_vectors,
    AVG(length(search_vector::text)) as avg_vector_length
FROM social_media_posts;
\echo ''

-- Check data quality issues
\echo 'Data Quality Issues:'
SELECT 
    COUNT(*) FILTER (WHERE id IS NULL) as null_ids,
    COUNT(*) FILTER (WHERE platform IS NULL) as null_platforms,
    COUNT(*) FILTER (WHERE url IS NULL OR url = '') as missing_urls,
    COUNT(*) FILTER (WHERE content IS NULL OR content = '') as empty_content,
    COUNT(*) FILTER (WHERE created_at IS NULL) as null_dates
FROM social_media_posts;
\echo ''

-- Sample of problematic records
\echo 'Sample Problematic Records:'
SELECT id, platform, LEFT(content, 50) as content_preview, 
       CASE 
           WHEN id IS NULL THEN 'NULL ID'
           WHEN platform IS NULL THEN 'NULL Platform'
           WHEN content = '' THEN 'Empty Content'
           ELSE 'Other'
       END as issue
FROM social_media_posts
WHERE id IS NULL OR platform IS NULL OR content = ''
LIMIT 5;
\echo ''

-- Language distribution (rough estimate based on content)
\echo 'Content Language Distribution (estimated):'
SELECT 
    COUNT(*) FILTER (WHERE content ~ '[א-ת]') as hebrew_content,
    COUNT(*) FILTER (WHERE content ~ '[ا-ي]') as arabic_content,
    COUNT(*) FILTER (WHERE content ~ '^[A-Za-z\s]+$') as english_only,
    COUNT(*) FILTER (WHERE content ~ '[^\x00-\x7F]') as non_ascii,
    COUNT(*) as total
FROM social_media_posts
WHERE content IS NOT NULL AND content != '';
\echo ''

-- Index analysis
\echo 'Search-Related Indexes:'
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'social_media_posts'
AND (indexname LIKE '%search%' OR indexdef LIKE '%tsvector%');
\echo ''

-- Check for triggers on search vector
\echo 'Search Vector Triggers:'
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'social_media_posts'
AND trigger_name LIKE '%search%';
\echo ''

-- Platform distribution
\echo 'Platform Distribution:'
SELECT 
    COALESCE(platform, 'NULL') as platform,
    COUNT(*) as post_count,
    COUNT(*) FILTER (WHERE content IS NOT NULL AND content != '') as with_content,
    COUNT(*) FILTER (WHERE jsonb_array_length(media_items) > 0) as with_media
FROM social_media_posts
GROUP BY platform
ORDER BY post_count DESC;
\echo ''

-- Search performance test
\echo 'Search Performance Test (searching for "gaza"):'
EXPLAIN (ANALYZE, BUFFERS) 
SELECT id, platform, content
FROM social_media_posts
WHERE search_vector @@ plainto_tsquery('english', 'gaza')
LIMIT 10;
