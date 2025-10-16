#!/usr/bin/env python3
"""
Debug script to check registration status
"""

import asyncio
import sqlite3
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from database_optimized import DatabaseOptimized

async def debug_registration_status():
    """Debug the registration status"""
    print("Debugging Registration Status")
    print("=" * 60)
    
    db_path = Config.DATABASE_PATH
    print(f"\nDatabase path: {db_path}")
    
    # Check direct SQL query
    print("\n1. Checking via direct SQL query:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT key, value FROM settings WHERE key = ?', ('registration_open',))
        row = cursor.fetchone()
        if row:
            print(f"   Found: key='{row[0]}', value='{row[1]}'")
            print(f"   Value type: {type(row[1])}")
            print(f"   Value lower: '{row[1].lower()}'")
            print(f"   Comparison (value.lower() == 'true'): {row[1].lower() == 'true'}")
        else:
            print("   ✗ No row found in settings table!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        conn.close()
    
    # Check via DatabaseOptimized
    print("\n2. Checking via DatabaseOptimized.get_registration_status():")
    db = DatabaseOptimized()
    try:
        is_open = await db.get_registration_status()
        print(f"   Result: {is_open}")
        print(f"   Type: {type(is_open)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Check all settings
    print("\n3. All settings in database:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM settings')
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"   {row}")
        else:
            print("   ✗ Settings table is empty!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        conn.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_registration_status())

