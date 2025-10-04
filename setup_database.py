#!/usr/bin/env python3
"""
Complete Database Schema Setup Script
This script creates the complete database schema that the bot expects.
"""

import sqlite3
import os

def setup_database():
    """Create the complete database schema"""
    db_file = 'vocalist_screening.db'
    
    # Remove the current database if it exists
    if os.path.exists(db_file):
        os.remove(db_file)
        print('✅ Old database removed')
    
    # Create a new database with the complete schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA synchronous=NORMAL;')
    cursor.execute('PRAGMA cache_size=-64000;')
    cursor.execute('PRAGMA temp_store=MEMORY;')
    cursor.execute('PRAGMA mmap_size=268435456;')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            state TEXT DEFAULT 'idle',
            name TEXT,
            address TEXT,
            phone TEXT,
            church TEXT,
            audio_file_id TEXT,
            audio_drive_link TEXT,
            audio_file_path TEXT,
            file_size INTEGER,
            audio_duration REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submission_count INTEGER DEFAULT 0,
            last_submission_at TIMESTAMP
        )
    ''')
    print('✅ Users table created')
    
    # Create submissions table
    cursor.execute('''
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            church TEXT NOT NULL,
            telegram_username TEXT,
            audio_file_path TEXT NOT NULL,
            audio_file_size INTEGER,
            audio_duration REAL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            reviewer_comments TEXT,
            reviewed_at TIMESTAMP,
            reviewed_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    print('✅ Submissions table created')
    
    # Create rate_limits table
    cursor.execute('''
        CREATE TABLE rate_limits (
            user_id INTEGER PRIMARY KEY,
            submission_count INTEGER DEFAULT 0,
            window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✅ Rate limits table created')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_state ON users(state)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at)')
    print('✅ Indexes created')
    
    conn.commit()
    conn.close()
    print('🎉 Complete database schema created successfully!')
    
    # Verify the schema
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute('PRAGMA table_info(users)')
    users_columns = [col[1] for col in cursor.fetchall()]
    print(f'Users table columns: {len(users_columns)} columns')
    
    # Check submissions table
    cursor.execute('PRAGMA table_info(submissions)')
    submissions_columns = [col[1] for col in cursor.fetchall()]
    print(f'Submissions table columns: {len(submissions_columns)} columns')
    
    # Check rate_limits table
    cursor.execute('PRAGMA table_info(rate_limits)')
    rate_limits_columns = [col[1] for col in cursor.fetchall()]
    print(f'Rate limits table columns: {len(rate_limits_columns)} columns')
    
    conn.close()
    print('✅ Database verification completed')

if __name__ == "__main__":
    print("🚀 Setting up complete database schema...")
    setup_database()
    print("✅ Database setup completed! You can now run the bot.")
