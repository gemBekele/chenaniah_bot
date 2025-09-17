import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config

class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table for storing conversation state
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    state TEXT DEFAULT 'idle',
                    name TEXT,
                    address TEXT,
                    phone TEXT,
                    audio_file_id TEXT,
                    audio_drive_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create submissions table for completed submissions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    telegram_username TEXT,
                    audio_drive_link TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    reviewer_comments TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's current state and data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def update_user_state(self, user_id: int, **kwargs) -> None:
        """Update user's state and data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get existing data
            existing = await self.get_user_state(user_id)
            if not existing:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (user_id, state) VALUES (?, ?)
                ''', (user_id, kwargs.get('state', 'idle')))
            
            # Update fields
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f'''
                UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', values)
            
            conn.commit()
    
    async def create_submission(self, user_id: int, name: str, address: str, 
                              phone: str, telegram_username: str, audio_drive_link: str) -> int:
        """Create a new submission record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO submissions 
                (user_id, name, address, phone, telegram_username, audio_drive_link)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, address, phone, telegram_username, audio_drive_link))
            
            submission_id = cursor.lastrowid
            conn.commit()
            return submission_id
    
    async def get_pending_submissions(self) -> list:
        """Get all pending submissions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions 
                WHERE status = 'pending' 
                ORDER BY submitted_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    async def update_submission_status(self, submission_id: int, status: str, 
                                     reviewer_comments: str = None) -> None:
        """Update submission status and reviewer comments"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE submissions 
                SET status = ?, reviewer_comments = ?
                WHERE id = ?
            ''', (status, reviewer_comments, submission_id))
            conn.commit()
    
    async def reset_user_state(self, user_id: int) -> None:
        """Reset user state to idle"""
        await self.update_user_state(user_id, state='idle', name=None, 
                                   address=None, phone=None, audio_file_id=None, 
                                   audio_drive_link=None)
