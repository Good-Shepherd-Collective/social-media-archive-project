#!/bin/bash
# Clear Python cache and restart the Telegram bot
# This ensures the bot uses the latest code changes

echo "🧹 Clearing Python cache and restarting bot..."
echo "=================================================="

# Get the directory of the script
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Step 1: Stop any running bot processes
echo ""
echo "🛑 Stopping any running bot processes..."
pkill -f "webhook_bot.py" 2>/dev/null || echo "   No bot processes found"
pkill -f "python.*twitter.*webhook" 2>/dev/null || echo "   No webhook processes found"

# Step 2: Clear Python cache
echo ""
echo "🗑️ Clearing Python cache..."

# Remove __pycache__ directories
echo "   Removing __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
echo "   ✅ __pycache__ directories cleared"

# Remove .pyc files
echo "   Removing .pyc files..."
find . -name "*.pyc" -type f -delete 2>/dev/null
echo "   ✅ .pyc files cleared"

# Remove .pyo files (optimized bytecode)
echo "   Removing .pyo files..."
find . -name "*.pyo" -type f -delete 2>/dev/null
echo "   ✅ .pyo files cleared"

# Step 3: Clear any import cache in memory (Python will do this on restart)
echo ""
echo "🔄 Python import cache will be cleared on restart"

# Step 4: Check for environment configuration
echo ""
echo "🔧 Checking environment configuration..."

if [ -f ".env.local" ]; then
    echo "   Found .env.local - will use LOCAL development mode"
    ENV_MODE="local"
    BOT_SCRIPT="run_local.sh"
elif [ -f ".env" ]; then
    echo "   Found .env - will use default configuration"
    ENV_MODE="default" 
    BOT_SCRIPT="start_webhook_bot.sh"
else
    echo "   ⚠️ No .env file found - please check configuration"
    ENV_MODE="unknown"
fi

# Step 5: Show what files were updated recently
echo ""
echo "📝 Recently updated Python files:"
find . -name "*.py" -type f -mtime -1 -exec ls -la {} + 2>/dev/null | head -10

# Step 6: Offer restart options
echo ""
echo "🚀 Ready to restart bot with fresh code!"
echo ""
echo "Choose restart option:"
echo "1) Start in LOCAL development mode (polling)"
echo "2) Start in WEBHOOK production mode"
echo "3) Just clear cache (don't restart)"
echo "4) Exit"
echo ""

# Function to start local mode
start_local() {
    echo ""
    echo "🔄 Starting bot in LOCAL development mode..."
    echo "   Mode: POLLING"
    echo "   Config: .env.local"
    echo "   Bot: @gsc_local_data_bot"
    echo ""
    
    # Set environment to use local config
    export ENV_FILE=".env.local"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo "   Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Start the bot
    echo "   Starting webhook_bot.py in polling mode..."
    python twitter/webhook_bot.py
}

# Function to start webhook mode
start_webhook() {
    echo ""
    echo "🔄 Starting bot in WEBHOOK production mode..."
    echo "   Mode: WEBHOOK"
    echo "   Config: .env"
    echo "   Port: 8443"
    echo ""
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo "   Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Start the bot
    echo "   Starting webhook_bot.py in webhook mode..."
    python twitter/webhook_bot.py
}

# Interactive mode if no arguments provided
if [ $# -eq 0 ]; then
    read -p "Enter choice (1-4): " choice
    case $choice in
        1)
            start_local
            ;;
        2)
            start_webhook
            ;;
        3)
            echo "✅ Cache cleared successfully! You can now manually start the bot."
            ;;
        4)
            echo "👋 Exiting without restart"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
else
    # Command line arguments mode
    case "$1" in
        "local"|"dev"|"development")
            start_local
            ;;
        "webhook"|"prod"|"production")
            start_webhook
            ;;
        "clear"|"cache")
            echo "✅ Cache cleared successfully!"
            ;;
        *)
            echo "Usage: $0 [local|webhook|clear]"
            echo "  local    - Start in local development mode"
            echo "  webhook  - Start in webhook production mode" 
            echo "  clear    - Just clear cache"
            exit 1
            ;;
    esac
fi

echo ""
echo "🎉 Cache clearing and restart completed!"
