#!/usr/bin/env python3
"""
Database Setup Script for Social Media Archive
Creates PostgreSQL database and tables for tweet storage with full-text search
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (without specifying database)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432)
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'social_media_archive'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE social_media_archive")
            print("✅ Created database 'social_media_archive'")
        else:
            print("✅ Database 'social_media_archive' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_tables():
    """Create tables and indexes"""
    try:
        # Connect to the social_media_archive database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432),
            database='social_media_archive'
        )
        cursor = conn.cursor()
        
        # Read and execute the schema file
        with open('database_schema.sql', 'r') as f:
            schema_sql = f.read()
            
        # Remove the CREATE DATABASE line since we already created it
        schema_sql = schema_sql.replace('CREATE DATABASE social_media_archive;', '')
        
        # Execute the schema
        cursor.execute(schema_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("✅ Database tables and indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False

def test_connection():
    """Test the database connection and show table info"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', 5432),
            database='social_media_archive'
        )
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print("✅ Database connection successful!")
        print("📊 Tables created:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    print("🚀 Setting up Social Media Archive Database")
    print("=" * 50)
    
    # Check if PostgreSQL is installed
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        sys.exit(1)
    
    # Create database
    if not create_database():
        sys.exit(1)
    
    # Setup tables
    if not setup_tables():
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    print("\n🎉 Database setup complete!")
    print("\n📝 Next steps:")
    print("1. Update your .env file with database credentials")
    print("2. Install PostgreSQL adapter: pip install psycopg2-binary")
    print("3. Test with: python verify_data.py")

if __name__ == "__main__":
    main()
