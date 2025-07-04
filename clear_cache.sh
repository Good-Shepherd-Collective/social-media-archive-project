#!/bin/bash
# Simple script to clear Python cache
# Use this when you just want to clear cache without restarting

echo "🧹 Clearing Python cache..."
echo "=========================="

# Get the directory of the script
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Stop any running bot processes
echo ""
echo "🛑 Stopping any running bot processes..."
pkill -f "webhook_bot.py" 2>/dev/null && echo "   ✅ Stopped webhook_bot.py" || echo "   ℹ️ No webhook_bot.py processes found"
pkill -f "python.*twitter.*webhook" 2>/dev/null && echo "   ✅ Stopped webhook processes" || echo "   ℹ️ No webhook processes found"

# Clear Python cache
echo ""
echo "🗑️ Clearing Python cache..."

# Remove __pycache__ directories
echo "   Removing __pycache__ directories..."
find . -name "__pycache__" -type d 2>/dev/null | while read dir; do
    rm -rf "$dir" && echo "     ✅ Removed $dir"
done

# Remove .pyc files
echo "   Removing .pyc files..."
find . -name "*.pyc" -type f 2>/dev/null | while read file; do
    rm -f "$file" && echo "     ✅ Removed $file"
done

# Remove .pyo files
echo "   Removing .pyo files..."
find . -name "*.pyo" -type f 2>/dev/null | while read file; do
    rm -f "$file" && echo "     ✅ Removed $file"
done

echo ""
echo "✅ Python cache cleared successfully!"
echo ""
echo "📝 Next steps:"
echo "   • Run './run_local.sh' for local development mode"
echo "   • Run './start_webhook_bot.sh' for production webhook mode"
echo "   • Or use './clear_cache_and_restart.sh' for interactive restart"
