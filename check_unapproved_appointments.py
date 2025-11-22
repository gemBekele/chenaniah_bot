#!/usr/bin/env python3
"""
Check for appointments booked by applicants who are not approved
This helps identify any appointments created before the approval check was added
"""

import sqlite3
import re
import os
import sys
from config import Config

def check_unapproved_appointments():
    """Check for appointments where the applicant's submission status is not 'approved'"""
    
    # Get database path from config
    db_path = Config.DATABASE_PATH
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print(f"   Please check DATABASE_PATH in .env or run from the correct directory")
        sys.exit(1)
    
    print(f"📊 Checking appointments for unapproved applicants...")
    print(f"   Database: {db_path}\n")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all appointments
    cursor.execute('''
        SELECT 
            id,
            applicant_name,
            applicant_phone,
            scheduled_date,
            scheduled_time,
            status,
            created_at
        FROM appointments
        ORDER BY created_at DESC
    ''')
    
    appointments = cursor.fetchall()
    
    if not appointments:
        print("⚠️  No appointments found in database")
        conn.close()
        return
    
    print(f"✅ Found {len(appointments)} total appointments\n")
    
    # Get all submissions
    cursor.execute('''
        SELECT 
            id,
            name,
            phone,
            status,
            submitted_at
        FROM submissions
    ''')
    
    submissions = cursor.fetchall()
    
    # Create a dictionary mapping phone (last 8 digits) to submission
    submission_map = {}
    for sub in submissions:
        sub_phone = sub['phone']
        sub_digits = re.sub(r'\D', '', sub_phone)
        if len(sub_digits) >= 8:
            last_8 = sub_digits[-8:]
            # Store submission with phone key
            if last_8 not in submission_map:
                submission_map[last_8] = []
            submission_map[last_8].append(sub)
    
    # Check each appointment
    unapproved_appointments = []
    no_submission_appointments = []
    
    for apt in appointments:
        apt_phone = apt['applicant_phone']
        apt_digits = re.sub(r'\D', '', apt_phone)
        
        if len(apt_digits) < 8:
            no_submission_appointments.append({
                'appointment': apt,
                'reason': 'Invalid phone format'
            })
            continue
        
        last_8 = apt_digits[-8:]
        
        # Find matching submission
        matching_submission = None
        if last_8 in submission_map:
            # Find exact match
            for sub in submission_map[last_8]:
                sub_phone = sub['phone']
                sub_digits = re.sub(r'\D', '', sub_phone)
                if len(sub_digits) >= 8 and sub_digits[-8:] == last_8:
                    matching_submission = sub
                    break
        
        if not matching_submission:
            no_submission_appointments.append({
                'appointment': apt,
                'reason': 'No matching submission found'
            })
        else:
            submission_status = matching_submission['status'].lower()
            if submission_status != 'approved':
                unapproved_appointments.append({
                    'appointment': apt,
                    'submission': matching_submission,
                    'status': submission_status
                })
    
    # Print results
    print("=" * 80)
    print(f"📋 SUMMARY")
    print("=" * 80)
    print(f"Total appointments: {len(appointments)}")
    print(f"Unapproved appointments: {len(unapproved_appointments)}")
    print(f"Appointments with no submission: {len(no_submission_appointments)}")
    print(f"Approved appointments: {len(appointments) - len(unapproved_appointments) - len(no_submission_appointments)}")
    print()
    
    if unapproved_appointments:
        print("=" * 80)
        print(f"⚠️  UNAPPROVED APPOINTMENTS ({len(unapproved_appointments)})")
        print("=" * 80)
        for item in unapproved_appointments:
            apt = item['appointment']
            sub = item['submission']
            status = item['status']
            print(f"\n📅 Appointment ID: {apt['id']}")
            print(f"   Name: {apt['applicant_name']}")
            print(f"   Phone: {apt['applicant_phone']}")
            print(f"   Scheduled: {apt['scheduled_date']} at {apt['scheduled_time']}")
            print(f"   Appointment Status: {apt['status']}")
            print(f"   Created: {apt['created_at']}")
            print(f"   └─ Submission Status: {status.upper()}")
            print(f"   └─ Submission ID: {sub['id']}")
            print(f"   └─ Submission Name: {sub['name']}")
            print(f"   └─ Submitted: {sub['submitted_at']}")
        print()
    
    if no_submission_appointments:
        print("=" * 80)
        print(f"❓ APPOINTMENTS WITH NO MATCHING SUBMISSION ({len(no_submission_appointments)})")
        print("=" * 80)
        for item in no_submission_appointments:
            apt = item['appointment']
            reason = item['reason']
            print(f"\n📅 Appointment ID: {apt['id']}")
            print(f"   Name: {apt['applicant_name']}")
            print(f"   Phone: {apt['applicant_phone']}")
            print(f"   Scheduled: {apt['scheduled_date']} at {apt['scheduled_time']}")
            print(f"   Created: {apt['created_at']}")
            print(f"   └─ Reason: {reason}")
        print()
    
    if not unapproved_appointments and not no_submission_appointments:
        print("✅ All appointments are from approved applicants!")
        print()
    
    conn.close()
    
    # Return count for scripting purposes
    return len(unapproved_appointments), len(no_submission_appointments)

if __name__ == '__main__':
    try:
        unapproved_count, no_submission_count = check_unapproved_appointments()
        if unapproved_count > 0 or no_submission_count > 0:
            sys.exit(1)  # Exit with error code if issues found
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

