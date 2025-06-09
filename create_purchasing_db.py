#!/usr/bin/env python3
"""
Create the ocs_purchasing database
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_purchasing_database():
    """Create the ocs_purchasing database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            user="ocs_user",
            password="ocs_pass",
            database="ocs_tickets"  # Connect to an existing database first
        )
        
        # Set autocommit mode to create database
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create cursor
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'ocs_purchasing'")
        exists = cursor.fetchone()
        
        if not exists:
            # Create the database
            cursor.execute("CREATE DATABASE ocs_purchasing")
            print("✅ Created ocs_purchasing database")
        else:
            print("ℹ️ ocs_purchasing database already exists")
        
        # Close connections
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating purchasing database: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ Creating OCS Purchasing Database")
    print("=" * 40)
    
    success = create_purchasing_database()
    
    if success:
        print("✅ Database setup completed successfully!")
    else:
        print("❌ Database setup failed!")
