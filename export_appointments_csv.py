#!/usr/bin/env python3
"""
Export all appointment/interview data to CSV file
Includes all applicant details and related information
"""

import sqlite3
import csv
import os
import sys
from datetime import datetime
from config import Config

def export_appointments_to_csv(output_file='appointments_export.csv'):
    """Export all appointments with full details to CSV"""
    
    # Get database path from config or environment
    db_path = Config.DATABASE_PATH
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print(f"   Please check DATABASE_PATH in .env or run from the correct directory")
        sys.exit(1)
    
    print(f"📊 Connecting to database: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all appointments with all fields
    cursor.execute('''
        SELECT 
            id,
            applicant_name,
            applicant_email,
            applicant_phone,
            scheduled_date,
            scheduled_time,
            status,
            notes,
            selected_song,
            additional_song,
            additional_song_singer,
            coordinator_verified,
            coordinator_verified_at,
            coordinator_approved,
            coordinator_approved_at,
            final_decision,
            decision_made_at,
            created_at,
            updated_at
        FROM appointments
        ORDER BY scheduled_date DESC, scheduled_time DESC
    ''')
    
    appointments = cursor.fetchall()
    
    if not appointments:
        print("⚠️  No appointments found in database")
        conn.close()
        return
    
    print(f"✅ Found {len(appointments)} appointments")
    
    # Get evaluations for each appointment
    evaluations_by_appointment = {}
    cursor.execute('''
        SELECT 
            appointment_id,
            judge_name,
            criteria_name,
            rating,
            comments,
            created_at
        FROM interview_evaluations
        ORDER BY appointment_id, judge_name, criteria_name
    ''')
    
    evaluations = cursor.fetchall()
    for eval_row in evaluations:
        apt_id = eval_row['appointment_id']
        if apt_id not in evaluations_by_appointment:
            evaluations_by_appointment[apt_id] = []
        evaluations_by_appointment[apt_id].append(eval_row)
    
    # Prepare CSV data
    csv_rows = []
    
    for apt in appointments:
        apt_id = apt['id']
        
        # Get evaluations for this appointment
        apt_evaluations = evaluations_by_appointment.get(apt_id, [])
        
        # Group evaluations by judge
        judge_evaluations = {}
        for eval_row in apt_evaluations:
            judge = eval_row['judge_name']
            if judge not in judge_evaluations:
                judge_evaluations[judge] = []
            judge_evaluations[judge].append(eval_row)
        
        # Create row with all appointment data
        row = {
            'ID': apt['id'],
            'Applicant Name': apt['applicant_name'] or '',
            'Applicant Email': apt['applicant_email'] or '',
            'Applicant Phone': apt['applicant_phone'] or '',
            'Scheduled Date': apt['scheduled_date'] or '',
            'Scheduled Time': apt['scheduled_time'] or '',
            'Status': apt['status'] or '',
            'Notes': apt['notes'] or '',
            'Selected Song': apt['selected_song'] or '',
            'Additional Song': apt['additional_song'] or '',
            'Additional Song Singer': apt['additional_song_singer'] or '',
            'Coordinator Verified (Attendance)': 'Yes' if apt['coordinator_verified'] else 'No',
            'Coordinator Verified At': apt['coordinator_verified_at'] or '',
            'Coordinator Approved': 'Yes' if apt['coordinator_approved'] else 'No',
            'Coordinator Approved At': apt['coordinator_approved_at'] or '',
            'Final Decision': apt['final_decision'] or '',
            'Decision Made At': apt['decision_made_at'] or '',
            'Created At': apt['created_at'] or '',
            'Updated At': apt['updated_at'] or '',
        }
        
        # Add evaluation data
        if judge_evaluations:
            # Add columns for each judge's evaluations
            for judge_name, evals in judge_evaluations.items():
                eval_text = []
                for eval_row in evals:
                    criteria = eval_row['criteria_name']
                    rating = eval_row['rating']
                    comments = eval_row['comments'] or ''
                    if comments:
                        eval_text.append(f"{criteria}: {rating}/5 ({comments})")
                    else:
                        eval_text.append(f"{criteria}: {rating}/5")
                
                row[f'Evaluations by {judge_name}'] = '; '.join(eval_text)
        else:
            row['Evaluations'] = 'No evaluations yet'
        
        csv_rows.append(row)
    
    # Write to CSV
    if csv_rows:
        fieldnames = list(csv_rows[0].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        print(f"✅ Exported {len(csv_rows)} appointments to: {output_file}")
        print(f"   File size: {os.path.getsize(output_file)} bytes")
    else:
        print("⚠️  No data to export")
    
    conn.close()

if __name__ == '__main__':
    # Get output filename from command line or use default
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'appointments_export.csv'
    
    # Add timestamp to filename if default
    if output_file == 'appointments_export.csv':
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'appointments_export_{timestamp}.csv'
    
    print("=" * 60)
    print("📋 Appointment/Interview CSV Export Tool")
    print("=" * 60)
    print()
    
    export_appointments_to_csv(output_file)
    
    print()
    print("=" * 60)
    print("✅ Export complete!")
    print("=" * 60)




