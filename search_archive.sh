#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if search term provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./search_archive.sh \"search terms\"${NC}"
    echo -e "Examples:"
    echo -e "  ./search_archive.sh \"palestine\""
    echo -e "  ./search_archive.sh \"gaza\""
    echo -e "  ./search_archive.sh \"cats\""
    exit 1
fi

SEARCH_TERM="$1"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}🔍 Searching Archive for: ${YELLOW}$SEARCH_TERM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# First, let's check what's searchable
echo -e "${CYAN}Searching in post content and notes...${NC}"
echo ""

# Perform the search using simple LIKE for now since search_vector seems to have issues
PGPASSWORD=$DB_PASSWORD psql -h localhost -U postgres -d social_media_archive -t -A -F"§" << SQL | while IFS='§' read -r id platform url content author created_at user_id notes tags media_count
SELECT 
    id,
    platform,
    url,
    COALESCE(content, ''),
    COALESCE(author_username, ''),
    to_char(created_at, 'YYYY-MM-DD HH24:MI') as created_at,
    telegram_user_id,
    COALESCE(raw_data->>'user_notes', '') as notes,
    COALESCE(array_to_string(user_hashtags, ' '), '') as tags,
    jsonb_array_length(media_items) as media_count
FROM social_media_posts
WHERE 
    platform IS NOT NULL 
    AND id IS NOT NULL
    AND (
        LOWER(content) LIKE LOWER('%$SEARCH_TERM%')
        OR LOWER(raw_data->>'user_notes') LIKE LOWER('%$SEARCH_TERM%')
        OR EXISTS (
            SELECT 1 FROM unnest(user_hashtags) tag 
            WHERE LOWER(tag) LIKE LOWER('%$SEARCH_TERM%')
        )
    )
ORDER BY created_at DESC
LIMIT 20;
SQL
do
    if [ ! -z "$id" ] && [ ! -z "$platform" ]; then
        echo -e "${GREEN}───────────────────────────────────────────────────────${NC}"
        
        # Header with platform and date
        if [ ! -z "$author" ] && [ "$author" != " " ]; then
            echo -e "📱 ${CYAN}$platform${NC} | 📅 $created_at | 👤 $author"
        else
            echo -e "📱 ${CYAN}$platform${NC} | 📅 $created_at | 👤 User: $user_id"
        fi
        
        # URL
        [ ! -z "$url" ] && echo -e "🔗 ${BLUE}$url${NC}"
        
        # Content - highlight search term
        if [ ! -z "$content" ] && [ "$content" != " " ]; then
            highlighted_content=$(echo "$content" | sed "s/$SEARCH_TERM/${RED}$SEARCH_TERM${NC}/gi")
            echo -e "📝 $highlighted_content"
        fi
        
        # User notes
        if [ ! -z "$notes" ] && [ "$notes" != " " ]; then
            highlighted_notes=$(echo "$notes" | sed "s/$SEARCH_TERM/${RED}$SEARCH_TERM${NC}/gi")
            echo -e "💭 ${YELLOW}Notes: $highlighted_notes${NC}"
        fi
        
        # Hashtags
        [ ! -z "$tags" ] && [ "$tags" != " " ] && echo -e "🏷️  ${YELLOW}Tags: $tags${NC}"
        
        # Media count
        [ "$media_count" -gt 0 ] 2>/dev/null && echo -e "🎥 Media files: $media_count"
        
        # Archive link
        if [ "$platform" = "twitter" ]; then
            json_file="tweet_${id}.json"
        else
            json_file="${platform}_${id}.json"
        fi
        echo -e "📂 Archive: ${BLUE}https://ov-ab103a.infomaniak.ch/data/${json_file}${NC}"
    fi
done

echo -e "${GREEN}───────────────────────────────────────────────────────${NC}"

# Show count
COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U postgres -d social_media_archive -t -c "
SELECT COUNT(*) FROM social_media_posts 
WHERE platform IS NOT NULL AND id IS NOT NULL
AND (
    LOWER(content) LIKE LOWER('%$SEARCH_TERM%')
    OR LOWER(raw_data->>'user_notes') LIKE LOWER('%$SEARCH_TERM%')
    OR EXISTS (
        SELECT 1 FROM unnest(user_hashtags) tag 
        WHERE LOWER(tag) LIKE LOWER('%$SEARCH_TERM%')
    )
)" | tr -d ' ')

echo ""
echo -e "${CYAN}Total results: ${GREEN}$COUNT${NC}"
echo ""
echo -e "${YELLOW}💡 Search includes:${NC} post content, user notes, and hashtags"
