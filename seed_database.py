#!/usr/bin/env python3
"""
Comprehensive Data Seeder for Chenaniah System
Creates dummy data for applications, appointments, and time slots
"""

import asyncio
import sqlite3
import random
from datetime import datetime, timedelta
from database_optimized import DatabaseOptimized

async def seed_database():
    """Seed the database with comprehensive dummy data for testing"""
    db = DatabaseOptimized()
    
    print("🌱 Starting comprehensive database seeding...")
    
    # Generate time slots for the next 30 days
    print("📅 Creating time slots for the next 30 days...")
    base_date = datetime.now().date()
    
    for day_offset in range(30):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Skip weekends for now
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue
            
        # Create time slots from 9:00 AM to 5:00 PM (30-minute intervals)
        for hour in range(9, 17):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                
                try:
                    await db.create_time_slot(time_str, date_str)
                    # Randomly make some slots unavailable (about 25% unavailable)
                    if random.choice([True, True, True, False]):
                        # Get the slot ID and update it to unavailable
                        slots = await db.get_time_slots(date_str)
                        for slot in slots:
                            if slot['time'] == time_str and slot['date'] == date_str:
                                await db.update_time_slot_availability(slot['id'], False)
                                break
                except Exception as e:
                    # Slot might already exist, that's okay
                    pass
    
    print("📝 Creating dummy applications (submissions)...")
    
    # Create dummy applications/submissions
    dummy_applications = [
        {
            "user_id": 1001,
            "name": "Abel Tesfaye",
            "address": "Bole, Addis Ababa",
            "phone": "+251-911-123-456",
            "church": "Ethiopian Orthodox Church",
            "telegram_username": "@abel_music",
            "audio_file_path": "audio/abel_audition.mp3",
            "audio_file_size": 2048000,
            "audio_duration": 120,
            "status": "pending"
        },
        {
            "user_id": 1002,
            "name": "Meron Getahun",
            "address": "Kazanchis, Addis Ababa",
            "phone": "+251-912-234-567",
            "church": "Addis Ababa Evangelical Church",
            "telegram_username": "@meron_sings",
            "audio_file_path": "audio/meron_audition.mp3",
            "audio_file_size": 1856000,
            "audio_duration": 95,
            "status": "approved"
        },
        {
            "user_id": 1003,
            "name": "Dawit Assefa",
            "address": "Merkato, Addis Ababa",
            "phone": "+251-913-345-678",
            "church": "Pentecostal Church",
            "telegram_username": "@dawit_worship",
            "audio_file_path": "audio/dawit_audition.mp3",
            "audio_file_size": 2560000,
            "audio_duration": 150,
            "status": "rejected"
        },
        {
            "user_id": 1004,
            "name": "Sara Tadesse",
            "address": "Piassa, Addis Ababa",
            "phone": "+251-914-456-789",
            "church": "Catholic Church",
            "telegram_username": "@sara_voice",
            "audio_file_path": "audio/sara_audition.mp3",
            "audio_file_size": 1920000,
            "audio_duration": 110,
            "status": "pending"
        },
        {
            "user_id": 1005,
            "name": "Yonas Bekele",
            "address": "Arat Kilo, Addis Ababa",
            "phone": "+251-915-567-890",
            "church": "Protestant Church",
            "telegram_username": "@yonas_music",
            "audio_file_path": "audio/yonas_audition.mp3",
            "audio_file_size": 2200000,
            "audio_duration": 135,
            "status": "approved"
        },
        {
            "user_id": 1006,
            "name": "Hanna Solomon",
            "address": "Cazanchis, Addis Ababa",
            "phone": "+251-916-678-901",
            "church": "Ethiopian Evangelical Church",
            "telegram_username": "@hanna_sings",
            "audio_file_path": "audio/hanna_audition.mp3",
            "audio_file_size": 1980000,
            "audio_duration": 105,
            "status": "pending"
        },
        {
            "user_id": 1007,
            "name": "Elias Worku",
            "address": "Bole, Addis Ababa",
            "phone": "+251-917-789-012",
            "church": "Orthodox Church",
            "telegram_username": "@elias_worship",
            "audio_file_path": "audio/elias_audition.mp3",
            "audio_file_size": 2400000,
            "audio_duration": 140,
            "status": "rejected"
        },
        {
            "user_id": 1008,
            "name": "Ruth Alemayehu",
            "address": "Kazanchis, Addis Ababa",
            "phone": "+251-918-890-123",
            "church": "Adventist Church",
            "telegram_username": "@ruth_voice",
            "audio_file_path": "audio/ruth_audition.mp3",
            "audio_file_size": 2100000,
            "audio_duration": 125,
            "status": "approved"
        },
        {
            "user_id": 1009,
            "name": "Samuel Girma",
            "address": "Merkato, Addis Ababa",
            "phone": "+251-919-901-234",
            "church": "Pentecostal Church",
            "telegram_username": "@samuel_music",
            "audio_file_path": "audio/samuel_audition.mp3",
            "audio_file_size": 2300000,
            "audio_duration": 130,
            "status": "pending"
        },
        {
            "user_id": 1010,
            "name": "Martha Yohannes",
            "address": "Piassa, Addis Ababa",
            "phone": "+251-920-012-345",
            "church": "Catholic Church",
            "telegram_username": "@martha_sings",
            "audio_file_path": "audio/martha_audition.mp3",
            "audio_file_size": 1950000,
            "audio_duration": 100,
            "status": "approved"
        }
    ]
    
    # Create applications in the database
    for app in dummy_applications:
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO submissions 
                    (user_id, name, address, phone, church, telegram_username, 
                     audio_file_path, audio_file_size, audio_duration, status, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app["user_id"],
                    app["name"],
                    app["address"],
                    app["phone"],
                    app["church"],
                    app["telegram_username"],
                    app["audio_file_path"],
                    app["audio_file_size"],
                    app["audio_duration"],
                    app["status"],
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            print(f"Error creating application for {app['name']}: {e}")
    
    print("👥 Creating dummy appointments...")
    
    # Create some dummy appointments
    dummy_appointments = [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+251-911-234-567",
            "date": (base_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "09:00",
            "notes": "Interested in vocal training",
            "status": "scheduled"
        },
        {
            "name": "Mary Johnson",
            "email": "mary.johnson@example.com",
            "phone": "+251-912-345-678",
            "date": (base_date + timedelta(days=2)).strftime('%Y-%m-%d'),
            "time": "10:30",
            "notes": "Has experience with traditional Ethiopian music",
            "status": "scheduled"
        },
        {
            "name": "David Smith",
            "email": "david.smith@example.com",
            "phone": "+251-913-456-789",
            "date": (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
            "time": "14:00",
            "notes": "Looking to join the worship team",
            "status": "completed"
        },
        {
            "name": "Sarah Wilson",
            "email": "sarah.wilson@example.com",
            "phone": "+251-914-567-890",
            "date": (base_date + timedelta(days=4)).strftime('%Y-%m-%d'),
            "time": "11:00",
            "notes": "Piano player interested in ministry",
            "status": "scheduled"
        },
        {
            "name": "Michael Brown",
            "email": "michael.brown@example.com",
            "phone": "+251-915-678-901",
            "date": (base_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            "time": "15:30",
            "notes": "No show - rescheduled",
            "status": "no_show"
        },
        {
            "name": "Emily Davis",
            "email": "emily.davis@example.com",
            "phone": "+251-916-789-012",
            "date": (base_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            "time": "09:30",
            "notes": "Cancelled due to emergency",
            "status": "cancelled"
        },
        {
            "name": "Abel Tesfaye",
            "email": "abel.tesfaye@example.com",
            "phone": "+251-911-123-456",
            "date": (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
            "time": "10:00",
            "notes": "Approved application - interview scheduled",
            "status": "scheduled"
        },
        {
            "name": "Meron Getahun",
            "email": "meron.getahun@example.com",
            "phone": "+251-912-234-567",
            "date": (base_date + timedelta(days=8)).strftime('%Y-%m-%d'),
            "time": "14:30",
            "notes": "Approved application - follow-up interview",
            "status": "completed"
        }
    ]
    
    for appointment in dummy_appointments:
        try:
            appointment_id = await db.create_appointment(
                appointment["name"],
                appointment["email"],
                appointment["phone"],
                appointment["date"],
                appointment["time"],
                appointment["notes"]
            )
            
            # Update status if not default
            if appointment["status"] != "scheduled":
                await db.update_appointment_status(appointment_id, appointment["status"])
                
        except Exception as e:
            print(f"Error creating appointment for {appointment['name']}: {e}")
    
    print("📊 Database seeding completed!")
    
    # Print comprehensive summary
    stats = await db.get_schedule_stats()
    print(f"\n📈 Schedule Summary:")
    print(f"   Total appointments: {stats['total_appointments']}")
    print(f"   Scheduled: {stats['scheduled']}")
    print(f"   Completed: {stats['completed']}")
    print(f"   Cancelled: {stats['cancelled']}")
    print(f"   No shows: {stats['no_show']}")
    
    # Get time slots count
    all_slots = await db.get_time_slots()
    available_slots = [slot for slot in all_slots if slot['available']]
    print(f"\n📅 Time Slots Summary:")
    print(f"   Total time slots: {len(all_slots)}")
    print(f"   Available slots: {len(available_slots)}")
    
    # Get applications count
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM submissions')
        total_apps = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "pending"')
        pending_apps = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "approved"')
        approved_apps = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = "rejected"')
        rejected_apps = cursor.fetchone()[0]
    
    print(f"\n📝 Applications Summary:")
    print(f"   Total applications: {total_apps}")
    print(f"   Pending: {pending_apps}")
    print(f"   Approved: {approved_apps}")
    print(f"   Rejected: {rejected_apps}")

if __name__ == "__main__":
    asyncio.run(seed_database())
