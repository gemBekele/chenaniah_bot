#!/usr/bin/env python3
"""
Migration script to add registration settings to existing database
"""

import sqlite3
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config

def migrate_database():
    """Add settings table and default registration status"""
    print("Starting database migration for registration settings...")
    
    db_path = Config.DATABASE_PATH
    print(f"Database path: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if settings table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='settings'
        ''')
        
        if cursor.fetchone():
            print("✓ Settings table already exists")
        else:
            print("✗ Settings table does not exist, creating it...")
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✓ Settings table created")
        
        # Check if registration_open setting exists
        cursor.execute('SELECT value FROM settings WHERE key = ?', ('registration_open',))
        row = cursor.fetchone()
        
        if row:
            print(f"✓ registration_open setting exists with value: {row[0]}")
        else:
            print("✗ registration_open setting does not exist, inserting default...")
            
            # Insert default registration status (open)
            cursor.execute('''
                INSERT INTO settings (key, value, updated_at) 
                VALUES ('registration_open', 'true', CURRENT_TIMESTAMP)
            ''')
            print("✓ registration_open setting inserted with default value: true")
        
        conn.commit()
        
        # Verify the setting
        cursor.execute('SELECT key, value, updated_at FROM settings WHERE key = ?', ('registration_open',))
        row = cursor.fetchone()
        
        print("\nFinal verification:")
        print(f"  Key: {row[0]}")
        print(f"  Value: {row[1]}")
        print(f"  Updated at: {row[2]}")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)

