#!/usr/bin/env python3
"""
Direct API test script to check if the API can read from the database
"""

import sys
import os
sys.path.append('.')

from database_optimized import DatabaseOptimized
import asyncio

async def test_api_database():
    """Test if the API can read from the database"""
    print("🧪 Testing API database connection...")
    print("=" * 50)
    
    try:
        # Initialize database
        db = DatabaseOptimized()
        print("✅ Database connection established")
        
        # Test getting all submissions
        print("\n📝 Testing get_all_submissions...")
        submissions = await db.get_all_submissions()
        print(f"   Found {len(submissions)} submissions")
        
        if submissions:
            print("   Recent submissions:")
            for sub in submissions[:5]:  # Show first 5
                print(f"     - ID {sub['id']}: {sub['name']} - Status: {sub['status']} - Submitted: {sub['submitted_at']}")
        else:
            print("   ❌ No submissions found!")
        
        # Test getting pending submissions
        print("\n⏳ Testing get_pending_submissions...")
        pending = await db.get_pending_submissions()
        print(f"   Found {len(pending)} pending submissions")
        
        # Test getting stats
        print("\n📊 Testing get_submission_stats...")
        stats = await db.get_submission_stats()
        print(f"   Stats: {stats}")
        
        # Test getting a specific submission
        if submissions:
            print(f"\n🔍 Testing get_submission_by_id for ID {submissions[0]['id']}...")
            specific = await db.get_submission_by_id(submissions[0]['id'])
            if specific:
                print(f"   ✅ Found submission: {specific['name']}")
            else:
                print("   ❌ Could not retrieve specific submission")
        
        print("\n✅ API database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_database():
    """Test database directly without async"""
    print("\n🔍 Testing database directly...")
    print("=" * 30)
    
    try:
        import sqlite3
        conn = sqlite3.connect('vocalist_screening.db')
        cursor = conn.cursor()
        
        # Check submissions
        cursor.execute('SELECT COUNT(*) FROM submissions')
        count = cursor.fetchone()[0]
        print(f"Direct database query: {count} submissions")
        
        if count > 0:
            cursor.execute('SELECT id, name, status, submitted_at FROM submissions ORDER BY submitted_at DESC LIMIT 3')
            subs = cursor.fetchall()
            print("Recent submissions:")
            for sub in subs:
                print(f"  - ID {sub[0]}: {sub[1]} - {sub[2]} - {sub[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting API database tests...")
    
    # Test direct database access
    direct_ok = test_direct_database()
    
    # Test async API database access
    async_ok = asyncio.run(test_api_database())
    
    print("\n" + "=" * 50)
    if direct_ok and async_ok:
        print("✅ All tests passed! Database is accessible.")
    else:
        print("❌ Some tests failed. Check the errors above.")
