#!/usr/bin/env python3
"""
Database inspection script to check if submissions exist
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    """Check what's in the database"""
    db_file = 'vocalist_screening.db'
    
    if not os.path.exists(db_file):
        print("❌ Database file not found!")
        return
    
    print("🔍 Checking database contents...")
    print("=" * 50)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check users table
    print("👥 USERS TABLE:")
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f"   Total users: {user_count}")
    
    if user_count > 0:
        cursor.execute('SELECT user_id, username, first_name, state, created_at FROM users ORDER BY created_at DESC LIMIT 5')
        users = cursor.fetchall()
        print("   Recent users:")
        for user in users:
            print(f"     - User {user[0]}: {user[1] or 'No username'} ({user[2] or 'No name'}) - State: {user[3]} - Created: {user[4]}")
    
    print()
    
    # Check submissions table
    print("📝 SUBMISSIONS TABLE:")
    cursor.execute('SELECT COUNT(*) FROM submissions')
    submission_count = cursor.fetchone()[0]
    print(f"   Total submissions: {submission_count}")
    
    if submission_count > 0:
        cursor.execute('SELECT id, user_id, name, status, submitted_at FROM submissions ORDER BY submitted_at DESC LIMIT 10')
        submissions = cursor.fetchall()
        print("   Recent submissions:")
        for sub in submissions:
            print(f"     - ID {sub[0]}: User {sub[1]} - {sub[2]} - Status: {sub[3]} - Submitted: {sub[4]}")
    else:
        print("   ❌ No submissions found!")
    
    print()
    
    # Check rate_limits table
    print("⏱️  RATE LIMITS TABLE:")
    cursor.execute('SELECT COUNT(*) FROM rate_limits')
    rate_limit_count = cursor.fetchone()[0]
    print(f"   Total rate limit records: {rate_limit_count}")
    
    if rate_limit_count > 0:
        cursor.execute('SELECT user_id, submission_count, last_action FROM rate_limits ORDER BY last_action DESC LIMIT 5')
        rate_limits = cursor.fetchall()
        print("   Recent rate limit activity:")
        for rl in rate_limits:
            print(f"     - User {rl[0]}: {rl[1]} submissions - Last action: {rl[2]}")
    
    print()
    
    # Check table schemas
    print("🗂️  TABLE SCHEMAS:")
    tables = ['users', 'submissions', 'rate_limits']
    for table in tables:
        cursor.execute(f'PRAGMA table_info({table})')
        columns = cursor.fetchall()
        print(f"   {table.upper()}:")
        for col in columns:
            print(f"     - {col[1]} ({col[2]})")
        print()
    
    # Check for any recent activity
    print("📊 RECENT ACTIVITY:")
    cursor.execute('''
        SELECT 
            'users' as table_name,
            COUNT(*) as count,
            MAX(created_at) as last_activity
        FROM users
        UNION ALL
        SELECT 
            'submissions' as table_name,
            COUNT(*) as count,
            MAX(submitted_at) as last_activity
        FROM submissions
        UNION ALL
        SELECT 
            'rate_limits' as table_name,
            COUNT(*) as count,
            MAX(last_action) as last_activity
        FROM rate_limits
    ''')
    
    activity = cursor.fetchall()
    for table, count, last_activity in activity:
        print(f"   {table}: {count} records, last activity: {last_activity or 'Never'}")
    
    conn.close()
    
    print("\n" + "=" * 50)
    if submission_count > 0:
        print("✅ Submissions found in database!")
        print("   The issue might be with the API server or admin dashboard.")
    else:
        print("❌ No submissions found in database!")
        print("   The bot might not be creating submissions properly.")
        print("   Check if users are completing the full submission process.")

if __name__ == "__main__":
    check_database()
