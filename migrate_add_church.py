#!/usr/bin/env python3
"""
Migration script to add church column to existing database
"""

import sqlite3
from config import Config

def migrate_database():
    """Add church column to users and submissions tables"""
    db_path = Config.DATABASE_PATH
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if church column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'church' not in columns:
            print("Adding 'church' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN church TEXT")
            print("✅ Added 'church' column to users table")
        else:
            print("✓ 'church' column already exists in users table")
        
        # Check if church column exists in submissions table
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'church' not in columns:
            print("Adding 'church' column to submissions table...")
            cursor.execute("ALTER TABLE submissions ADD COLUMN church TEXT")
            print("✅ Added 'church' column to submissions table")
        else:
            print("✓ 'church' column already exists in submissions table")
        
        conn.commit()
        print("\n✅ Database migration completed successfully!")

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()

