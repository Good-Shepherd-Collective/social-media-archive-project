#!/usr/bin/env python3
"""
Test script to demonstrate the environment-aware storage system
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path to import storage_utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from storage_utils import storage_manager

def test_storage():
    """Test the storage configuration"""
    print("🔧 Storage Configuration Test")
    print("=" * 40)
    
    # Show current configuration
    print(f"Environment: {storage_manager.environment}")
    print(f"Local path: {storage_manager.local_path}")
    print(f"Server path: {storage_manager.server_path}")
    print(f"Info: {storage_manager.get_environment_info()}")
    print()
    
    # Test paths for a sample tweet
    test_tweet_id = "123456789"
    paths = storage_manager.get_storage_paths(f"tweet_{test_tweet_id}.json")
    
    print(f"For tweet ID {test_tweet_id}, data would be saved to:")
    for i, path in enumerate(paths, 1):
        print(f"  {i}. {path}")
    
    print()
    print("To change environment, set ENVIRONMENT variable to:")
    print("  - 'local': Save only to local path")
    print("  - 'server': Save only to server path") 
    print("  - 'both': Save to both locations (default)")
    print()
    print("Example:")
    print("  export ENVIRONMENT=local")
    print("  export ENVIRONMENT=server")
    print("  export ENVIRONMENT=both")

if __name__ == "__main__":
    test_storage()
