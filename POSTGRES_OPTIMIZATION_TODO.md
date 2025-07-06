# PostgreSQL Full-Text Search Optimization TODO

This document outlines the necessary optimizations for implementing robust full-text search functionality for the social media archive, preparing for front-end integration.

## 🔍 Current State
- ✅ Basic `tsvector` column exists (`search_vector`)
- ✅ Basic index exists (`idx_posts_search`)
- ⚠️ Search vectors appear to be poorly populated
- ⚠️ No triggers for automatic vector updates
- ⚠️ No configuration for language-specific parsing

## 📋 TODO List

### 1. Fix Search Vector Population
- [ ] Audit current `search_vector` data quality
- [ ] Create proper trigger function to automatically update search vectors
- [ ] Backfill all existing posts with properly formatted search vectors
- [ ] Include all searchable fields in vector:
  - Post content
  - User notes
  - Author username
  - Hashtags (both scraped and user)
  - Platform name

### 2. Optimize Search Configuration
- [ ] Configure language-specific text search configurations
  ```sql
  -- Support for multiple languages (English, Arabic, Hebrew, etc.)
  ALTER TABLE social_media_posts ADD COLUMN search_vector_en tsvector;
  ALTER TABLE social_media_posts ADD COLUMN search_vector_ar tsvector;
  ALTER TABLE social_media_posts ADD COLUMN search_vector_he tsvector;
  ```
- [ ] Set appropriate weights for different fields
  ```sql
  -- Example: title/username gets weight A, content gets B, hashtags get C
  setweight(to_tsvector('english', coalesce(content,'')), 'B') ||
  setweight(to_tsvector('english', coalesce(author_username,'')), 'A')
  ```

### 3. Create Comprehensive Indexes
- [ ] GIN index on search vector (better for searches)
  ```sql
  CREATE INDEX idx_posts_search_gin ON social_media_posts USING GIN(search_vector);
  ```
- [ ] Partial indexes for platform-specific searches
- [ ] Index on created_at for time-based filtering
- [ ] Compound indexes for common query patterns

### 4. Add Search-Specific Columns
- [ ] Add `language` column to detect post language
- [ ] Add `search_keywords` column for manual keyword additions
- [ ] Add `search_rank` column for custom ranking
- [ ] Add `embeddings` column for future ML-based semantic search

### 5. Create Search Functions
- [ ] Create stored procedure for complex searches
  ```sql
  CREATE FUNCTION search_posts(
    query TEXT,
    platforms TEXT[],
    date_from TIMESTAMP,
    date_to TIMESTAMP,
    limit_count INT
  ) RETURNS TABLE(...);
  ```
- [ ] Create function for "more like this" searches
- [ ] Create function for trending hashtag analysis

### 6. Performance Optimizations
- [ ] Implement search result caching table
- [ ] Add materialized views for common searches
- [ ] Configure PostgreSQL for better FTS performance:
  - [ ] Increase `work_mem` for complex queries
  - [ ] Tune `shared_buffers`
  - [ ] Configure autovacuum for search tables

### 7. Data Quality Improvements
- [ ] Clean up malformed posts in database
- [ ] Standardize platform names
- [ ] Fix posts with missing IDs or platforms
- [ ] Remove duplicate entries
- [ ] Validate and fix URL formats

### 8. Search Features for Front-End
- [ ] Implement faceted search capabilities:
  - Platform filters
  - Date range filters
  - Media type filters
  - User filters
  - Hashtag filters
- [ ] Add search suggestions/autocomplete data
- [ ] Create search analytics table
- [ ] Implement saved searches functionality

### 9. API Preparation
- [ ] Create views for front-end consumption
  ```sql
  CREATE VIEW searchable_posts AS
  SELECT id, platform, url, content, author_username,
         created_at, media_count, hashtags, 
         ts_rank(search_vector, query) as relevance
  FROM social_media_posts;
  ```
- [ ] Add JSON aggregation functions for media items
- [ ] Create read-only user for front-end queries
- [ ] Implement row-level security if needed

### 10. Advanced Features
- [ ] Implement synonym dictionary for better matching
- [ ] Add spelling correction suggestions
- [ ] Create thesaurus for related terms
- [ ] Add support for phrase searches
- [ ] Implement proximity searches
- [ ] Add wildcard and regex search support

### 11. Monitoring & Maintenance
- [ ] Create search query log table
- [ ] Add slow query monitoring
- [ ] Create maintenance scripts for:
  - Rebuilding search vectors
  - Updating statistics
  - Cleaning old search logs
- [ ] Set up alerts for search performance issues

### 12. Documentation
- [ ] Document search syntax for users
- [ ] Create API documentation for front-end developers
- [ ] Document maintenance procedures
- [ ] Create search performance benchmarks

## 🚀 Implementation Priority

### Phase 1 (Critical - Do First)
1. Fix search vector population (#1)
2. Create proper indexes (#3)
3. Clean up data quality issues (#7)

### Phase 2 (Core Features)
4. Add search functions (#5)
5. Configure language support (#2)
6. Create API views (#9)

### Phase 3 (Enhanced Features)
7. Add advanced search features (#10)
8. Implement faceted search (#8)
9. Add monitoring (#11)

## 📊 Success Metrics
- Search queries return results in <100ms
- Search accuracy >90% for exact terms
- Support for 10k+ concurrent searches
- Zero downtime during reindexing
- Multi-language support (English, Arabic, Hebrew minimum)

## 🔧 Testing Requirements
- [ ] Create test dataset with known search results
- [ ] Benchmark current vs optimized performance
- [ ] Test Arabic language search accuracy
- [ ] Test search under load
- [ ] Validate all edge cases (special characters, emojis, etc.)

## 📝 Notes
- Current database has 28 posts (as of last check)
- Mixed quality data with some malformed entries
- Need to coordinate with front-end team on API requirements
- Consider using PostgreSQL 15+ features for better JSON handling

## 🌐 Multi-Language Search Considerations

### Language Support Priority:
1. **English** - Currently configured (default)
2. **Arabic** - 10 posts identified, RTL support needed
3. **Hebrew** - Expected content, RTL support needed

### RTL (Right-to-Left) Language Specifics:
- [ ] Configure proper text direction handling
- [ ] Ensure search highlighting works correctly with RTL text
- [ ] Test mixed LTR/RTL content (common in social media)
- [ ] Handle language detection for mixed-language posts

### Language Detection Strategy:
```sql
-- Add language detection
ALTER TABLE social_media_posts ADD COLUMN detected_language VARCHAR(10);
ALTER TABLE social_media_posts ADD COLUMN is_multilingual BOOLEAN DEFAULT FALSE;

-- Create function to detect primary language
CREATE FUNCTION detect_post_language(content TEXT) 
RETURNS VARCHAR(10) AS $$
BEGIN
  -- Logic to detect Hebrew, Arabic, or English
  -- Can use character ranges or external libraries
END;
$$ LANGUAGE plpgsql;
```

### Search Strategy for Multi-Language:
1. Auto-detect language per post
2. Create language-specific search vectors
3. Search across all language vectors when querying
4. Provide language filter in front-end
