import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from threading import Lock
from contextlib import contextmanager
from config import Config
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimized:
    """Optimized database with connection pooling, WAL mode, and better concurrency"""
    
    def __init__(self, db_path: str = None, pool_size: int = 10):
        self.db_path = db_path or Config.DATABASE_PATH
        self.pool_size = pool_size
        self._lock = Lock()
        self._connection_pool = []
        self.init_database()
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """Initialize connection pool for better concurrency"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            self._connection_pool.append(conn)
        logger.info(f"Initialized database connection pool with {self.pool_size} connections")
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        with self._lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
            else:
                # Create new connection if pool is empty
                conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
                conn.row_factory = sqlite3.Row
                logger.warning("Connection pool exhausted, creating new connection")
        
        try:
            yield conn
        finally:
            with self._lock:
                if len(self._connection_pool) < self.pool_size:
                    self._connection_pool.append(conn)
                else:
                    conn.close()
    
    def init_database(self):
        """Initialize the database with required tables and optimizations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute('PRAGMA journal_mode=WAL;')
        
        # Optimize SQLite settings
        cursor.execute('PRAGMA synchronous=NORMAL;')  # Faster writes
        cursor.execute('PRAGMA cache_size=-64000;')   # 64MB cache
        cursor.execute('PRAGMA temp_store=MEMORY;')   # Use memory for temp tables
        cursor.execute('PRAGMA mmap_size=268435456;') # 256MB memory-mapped I/O
        
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
        
        # Create submissions table for completed submissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
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
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_state ON users(state)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at)')
        
        # Create rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id INTEGER PRIMARY KEY,
                submission_count INTEGER DEFAULT 0,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create settings table for system configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default registration status (open)
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('registration_open', 'true')
        ''')

        # Insert default SMS settings
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('sms_enabled', 'false')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('sms_sender_id', '')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('sms_template_approved', 'Dear {name}, your application has been approved. - Chenaniah')
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value)
            VALUES ('sms_template_rejected', 'Dear {name}, your application was not approved at this time. - Chenaniah')
        ''')
        
        # Create scheduling tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                label TEXT NOT NULL,
                date TEXT NOT NULL,
                available BOOLEAN DEFAULT 1,
                period TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(time, date)
            )
        ''')
        
        # Add period column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute('ALTER TABLE time_slots ADD COLUMN period TEXT')
            logger.info("Added period column to time_slots table")
        except sqlite3.OperationalError:
            # Column already exists, skip
            pass
        
        # Add location column if it doesn't exist (migration for existing databases)
        try:
            cursor.execute('ALTER TABLE time_slots ADD COLUMN location TEXT')
            logger.info("Added location column to time_slots table")
        except sqlite3.OperationalError:
            # Column already exists, skip
            pass
        
        # Migrate existing slots to have period set
        # Also update ALL existing slots to new period definition (afternoon starts at 2:00 PM)
        # This ensures all slots are updated when the definition changes
        # IMPORTANT: This runs on every startup to ensure all slots have correct period
        try:
            # Extract hours from time string (HH:MM format) and set period
            # Morning: 9:00 AM - 1:59 PM (09:00 - 13:59)
            # Afternoon: 2:00 PM - 5:00 PM (14:00 - 17:00)
            cursor.execute('''
                UPDATE time_slots 
                SET period = CASE 
                    WHEN CAST(SUBSTR(time, 1, 2) AS INTEGER) >= 9 
                         AND CAST(SUBSTR(time, 1, 2) AS INTEGER) < 14 THEN 'morning'
                    WHEN CAST(SUBSTR(time, 1, 2) AS INTEGER) >= 14 
                         AND CAST(SUBSTR(time, 1, 2) AS INTEGER) <= 17 THEN 'afternoon'
                    ELSE NULL
                END
            ''')
            rows_updated = cursor.rowcount
            conn.commit()  # Ensure the update is committed
            if rows_updated > 0:
                logger.info(f"✅ Updated period for {rows_updated} time slots (afternoon starts at 2:00 PM)")
            else:
                logger.info("No time slots found to update")
        except Exception as e:
            logger.error(f"❌ Could not migrate period for existing slots: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_name TEXT NOT NULL,
                applicant_email TEXT NOT NULL,
                applicant_phone TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                selected_song TEXT,
                additional_song TEXT,
                additional_song_singer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add new columns to existing table if they don't exist (migration)
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN selected_song TEXT')
            conn.commit()
            logger.info("✅ Added selected_song column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add selected_song column: {e}")
            # Column already exists, which is fine
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song TEXT')
            conn.commit()
            logger.info("✅ Added additional_song column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add additional_song column: {e}")
            # Column already exists, which is fine
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song_singer TEXT')
            conn.commit()
            logger.info("✅ Added additional_song_singer column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add additional_song_singer column: {e}")
            # Column already exists, which is fine
        
        # Add attendance and approval columns
        # coordinator_verified is used for attendance_checked (backward compatibility)
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN coordinator_verified BOOLEAN DEFAULT 0')
            conn.commit()
            logger.info("✅ Added coordinator_verified (attendance_checked) column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add coordinator_verified column: {e}")
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN coordinator_verified_at TIMESTAMP')
            conn.commit()
            logger.info("✅ Added coordinator_verified_at (attendance_checked_at) column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add coordinator_verified_at column: {e}")
        
        # Add coordinator_approved column for approval status
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN coordinator_approved BOOLEAN DEFAULT 0')
            conn.commit()
            logger.info("✅ Added coordinator_approved column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add coordinator_approved column: {e}")
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN coordinator_approved_at TIMESTAMP')
            conn.commit()
            logger.info("✅ Added coordinator_approved_at column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add coordinator_approved_at column: {e}")
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN final_decision TEXT DEFAULT NULL')
            conn.commit()
            logger.info("✅ Added final_decision column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add final_decision column: {e}")
        
        try:
            cursor.execute('ALTER TABLE appointments ADD COLUMN decision_made_at TIMESTAMP')
            conn.commit()
            logger.info("✅ Added decision_made_at column to appointments table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"Could not add decision_made_at column: {e}")
        
        # Create interview_evaluations table for storing judge ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL,
                judge_name TEXT NOT NULL,
                criteria_name TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 0 AND rating <= 5),
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id),
                UNIQUE(appointment_id, judge_name, criteria_name)
            )
        ''')
        
        # Create indexes for scheduling tables
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_slots_date ON time_slots(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_slots_available ON time_slots(available)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_coordinator_verified ON appointments(coordinator_verified)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_appointment_id ON interview_evaluations(appointment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_evaluations_judge_name ON interview_evaluations(judge_name)')
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized with optimizations (WAL mode, indexes, connection pool)")
    
    async def check_rate_limit(self, user_id: int, max_submissions: int = 3, window_hours: int = 24) -> tuple[bool, str]:
        """Check if user is within rate limits"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create rate limit record
            cursor.execute('SELECT * FROM rate_limits WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            current_time = datetime.now()
            
            if not row:
                # First time user
                cursor.execute('''
                    INSERT INTO rate_limits (user_id, submission_count, window_start, last_action)
                    VALUES (?, 0, ?, ?)
                ''', (user_id, current_time, current_time))
                conn.commit()
                return True, "OK"
            
            window_start = datetime.fromisoformat(row['window_start'])
            submission_count = row['submission_count']
            
            # Check if window has expired
            if current_time - window_start > timedelta(hours=window_hours):
                # Reset window
                cursor.execute('''
                    UPDATE rate_limits 
                    SET submission_count = 0, window_start = ?, last_action = ?
                    WHERE user_id = ?
                ''', (current_time, current_time, user_id))
                conn.commit()
                return True, "OK"
            
            # Check if limit exceeded
            if submission_count >= max_submissions:
                remaining_time = timedelta(hours=window_hours) - (current_time - window_start)
                hours = int(remaining_time.total_seconds() // 3600)
                minutes = int((remaining_time.total_seconds() % 3600) // 60)
                return False, f"Rate limit exceeded. Try again in {hours}h {minutes}m"
            
            return True, "OK"
    
    async def increment_rate_limit(self, user_id: int):
        """Increment rate limit counter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE rate_limits 
                SET submission_count = submission_count + 1, last_action = ?
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            conn.commit()
    
    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's current state and data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def update_user_state(self, user_id: int, **kwargs) -> None:
        """Update user's state and data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get existing data
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing = cursor.fetchone()
            
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
                              phone: str, church: str, telegram_username: str, 
                              audio_file_path: str, audio_file_size: int = 0,
                              audio_duration: float = 0) -> int:
        """Create a new submission record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO submissions 
                (user_id, name, address, phone, church, telegram_username, 
                 audio_file_path, audio_file_size, audio_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, address, phone, church, telegram_username, 
                  audio_file_path, audio_file_size, audio_duration))
            
            submission_id = cursor.lastrowid
            
            # Update user submission count
            cursor.execute('''
                UPDATE users 
                SET submission_count = submission_count + 1,
                    last_submission_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            return submission_id
    
    async def get_pending_submissions(self) -> list:
        """Get all pending submissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions 
                WHERE status = 'pending' 
                ORDER BY submitted_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_all_submissions(self, status: str = None, search_query: str = None, limit: int = 10000, offset: int = 0) -> list:
        """Get all submissions with optional status filter and search"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build the query dynamically based on filters
            base_query = 'SELECT * FROM submissions'
            conditions = []
            params = []
            
            if status:
                conditions.append('status = ?')
                params.append(status)
            
            if search_query:
                search_condition = '''(
                    LOWER(name) LIKE LOWER(?) OR 
                    LOWER(phone) LIKE LOWER(?) OR 
                    LOWER(church) LIKE LOWER(?) OR 
                    LOWER(address) LIKE LOWER(?) OR 
                    LOWER(telegram_username) LIKE LOWER(?)
                )'''
                conditions.append(search_condition)
                search_param = f'%{search_query}%'
                params.extend([search_param] * 5)  # Add search_param 5 times for each field
            
            if conditions:
                base_query += ' WHERE ' + ' AND '.join(conditions)
            
            base_query += ' ORDER BY submitted_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_submission_count(self, status: str = None, search_query: str = None) -> int:
        """Get total count of submissions with optional status filter and search"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build the query dynamically based on filters
            base_query = 'SELECT COUNT(*) FROM submissions'
            conditions = []
            params = []
            
            if status:
                conditions.append('status = ?')
                params.append(status)
            
            if search_query:
                search_condition = '''(
                    LOWER(name) LIKE LOWER(?) OR 
                    LOWER(phone) LIKE LOWER(?) OR 
                    LOWER(church) LIKE LOWER(?) OR 
                    LOWER(address) LIKE LOWER(?) OR 
                    LOWER(telegram_username) LIKE LOWER(?)
                )'''
                conditions.append(search_condition)
                search_param = f'%{search_query}%'
                params.extend([search_param] * 5)  # Add search_param 5 times for each field
            
            if conditions:
                base_query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(base_query, params)
            return cursor.fetchone()[0]
    
    async def get_submission_by_id(self, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get a single submission by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def update_submission_status(self, submission_id: int, status: str, 
                                     reviewer_comments: str = None,
                                     reviewed_by: str = None) -> None:
        """Update submission status and reviewer comments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE submissions 
                SET status = ?, reviewer_comments = ?, 
                    reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
                WHERE id = ?
            ''', (status, reviewer_comments, reviewed_by, submission_id))
            conn.commit()
    
    async def get_submission_stats(self) -> Dict[str, int]:
        """Get statistics about submissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
                FROM submissions
            ''')
            row = cursor.fetchone()
            return {
                'total': row[0] or 0,
                'pending': row[1] or 0,
                'approved': row[2] or 0,
                'rejected': row[3] or 0
            }
    
    async def reset_user_state(self, user_id: int) -> None:
        """Reset user state to idle"""
        await self.update_user_state(user_id, state='idle', name=None, 
                                   address=None, phone=None, audio_file_id=None, 
                                   audio_drive_link=None, audio_file_path=None)
    
    async def get_registration_status(self) -> bool:
        """Get current registration status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', ('registration_open',))
            row = cursor.fetchone()
            return row and row[0].lower() == 'true'
    
    async def set_registration_status(self, is_open: bool) -> None:
        """Set registration status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', ('registration_open', 'true' if is_open else 'false'))
            conn.commit()

    async def get_sms_settings(self) -> dict:
        """Return SMS settings (enabled, sender_id, templates)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            keys = [
                'sms_enabled',
                'sms_sender_id',
                'sms_template_approved',
                'sms_template_rejected',
            ]
            placeholders = ','.join('?' for _ in keys)
            cursor.execute(f'SELECT key, value FROM settings WHERE key IN ({placeholders})', keys)
            rows = cursor.fetchall()
            result = {row['key']: row['value'] for row in rows}
            return {
                'enabled': (result.get('sms_enabled', 'false').lower() == 'true'),
                'sender_id': result.get('sms_sender_id', ''),
                'template_approved': result.get('sms_template_approved', ''),
                'template_rejected': result.get('sms_template_rejected', ''),
            }

    async def set_sms_settings(self, enabled: bool, sender_id: str, template_approved: str, template_rejected: str) -> None:
        """Update SMS settings atomically"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = [
                ('sms_enabled', 'true' if enabled else 'false'),
                ('sms_sender_id', sender_id or ''),
                ('sms_template_approved', template_approved or ''),
                ('sms_template_rejected', template_rejected or ''),
            ]
            for key, value in updates:
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
            conn.commit()
    
    # Scheduling Methods
    
    async def get_schedule_stats(self) -> Dict[str, int]:
        """Get scheduling statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get appointment counts by status
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_appointments,
                    SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) as no_show
                FROM appointments
            ''')
            
            result = cursor.fetchone()
            return {
                'total_appointments': result[0] or 0,
                'scheduled': result[1] or 0,
                'accepted': result[2] or 0,  # completed = accepted
                'rejected': result[4] or 0,  # no_show = rejected
                'cancelled': result[3] or 0
            }
    
    async def get_appointments(self, search_query: str = None) -> List[Dict[str, Any]]:
        """Get all interview appointments with optional search"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure song columns exist (migration)
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN selected_song TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song_singer TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Build query
            query = '''
                SELECT id, applicant_name, applicant_email, applicant_phone, 
                       scheduled_date, scheduled_time, status, notes, 
                       selected_song, additional_song, additional_song_singer,
                       coordinator_verified, coordinator_verified_at,
                       coordinator_approved, coordinator_approved_at,
                       final_decision, decision_made_at,
                       created_at, updated_at
                FROM appointments 
            '''
            
            params = []
            if search_query:
                query += '''
                    WHERE LOWER(applicant_name) LIKE LOWER(?) OR 
                          LOWER(applicant_phone) LIKE LOWER(?)
                '''
                search_param = f'%{search_query}%'
                params.extend([search_param, search_param])
            
            query += ' ORDER BY scheduled_date DESC, scheduled_time DESC'
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            # Convert Row objects to dictionaries
            return [dict(row) for row in rows]
    
    async def get_appointments_by_phone(self, applicant_phone: str) -> List[Dict[str, Any]]:
        """Get all appointments for a given phone number"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Extract last 8 digits from phone number for matching
            import re
            digits_only = re.sub(r'\D', '', applicant_phone)
            if len(digits_only) < 8:
                return []
            
            last_8_digits = digits_only[-8:]
            
            # Create a pattern that matches the digits with any characters in between
            # e.g. 1234 -> %1%2%3%4
            like_pattern = '%' + '%'.join(list(last_8_digits))
            
            cursor.execute('''
                SELECT id, applicant_name, applicant_email, applicant_phone, 
                       scheduled_date, scheduled_time, status, notes, 
                       selected_song, additional_song, additional_song_singer,
                       coordinator_verified, coordinator_verified_at,
                       coordinator_approved, coordinator_approved_at,
                       final_decision, decision_made_at,
                       created_at, updated_at
                FROM appointments 
                WHERE applicant_phone LIKE ?
                ORDER BY scheduled_date DESC, scheduled_time DESC
            ''', (like_pattern,))
            
            rows = cursor.fetchall()
            # Convert Row objects to dictionaries
            appointments = [dict(row) for row in rows]
            
            # Filter to only exact matches (last 8 digits)
            filtered_appointments = []
            for apt in appointments:
                apt_phone = apt.get('applicant_phone', '')
                apt_digits = re.sub(r'\D', '', apt_phone)
                if len(apt_digits) >= 8 and apt_digits[-8:] == last_8_digits:
                    filtered_appointments.append(apt)
            
            return filtered_appointments
    
    async def create_appointment(self, applicant_name: str, applicant_email: str, 
                                applicant_phone: str, scheduled_date: str, 
                                scheduled_time: str, notes: str = "",
                                selected_song: str = "", additional_song: str = "",
                                additional_song_singer: str = "") -> Optional[int]:
        """Create a new interview appointment"""
        logger.info(f"Saving appointment - selected_song: {selected_song}, additional_song: {additional_song}, singer: {additional_song_singer}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ensure song columns exist before inserting
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN selected_song TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE appointments ADD COLUMN additional_song_singer TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass
            
            cursor.execute('''
                INSERT INTO appointments 
                (applicant_name, applicant_email, applicant_phone, scheduled_date, 
                 scheduled_time, status, notes, selected_song, additional_song, 
                 additional_song_singer, created_at)
                VALUES (?, ?, ?, ?, ?, 'scheduled', ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (applicant_name, applicant_email, applicant_phone, scheduled_date, 
                  scheduled_time, notes, selected_song, additional_song, 
                  additional_song_singer))
            conn.commit()
            appointment_id = cursor.lastrowid
            logger.info(f"Appointment created with ID: {appointment_id}")
            return appointment_id
    
    async def update_appointment_status(self, appointment_id: int, status: str) -> bool:
        """Update appointment status and sync final_decision"""
        final_decision = None
        if status == 'completed':
            final_decision = 'accepted'
        elif status == 'no_show':
            final_decision = 'rejected'
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if final_decision:
                cursor.execute('''
                    UPDATE appointments 
                    SET status = ?, final_decision = ?, decision_made_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, final_decision, appointment_id))
            else:
                cursor.execute('''
                    UPDATE appointments 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
    
    async def get_time_slots(self, date: str = None) -> List[Dict[str, Any]]:
        """Get time slots for a specific date or all dates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if date:
                cursor.execute('''
                    SELECT * FROM time_slots 
                    WHERE date = ?
                    ORDER BY time
                ''', (date,))
            else:
                cursor.execute('''
                    SELECT * FROM time_slots 
                    ORDER BY date DESC, time
                ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    async def create_time_slot(self, time: str, date: str, location: str = None) -> bool:
        """Create a new time slot"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if slot already exists
            cursor.execute('''
                SELECT id FROM time_slots 
                WHERE time = ? AND date = ?
            ''', (time, date))
            
            if cursor.fetchone():
                return False  # Slot already exists
            
            # Create time label from time
            time_obj = datetime.strptime(time, '%H:%M')
            label = time_obj.strftime('%I:%M %p').lstrip('0')
            
            # Determine period (morning or afternoon)
            # Morning: 9:00 AM - 1:59 PM (09:00 - 13:59)
            # Afternoon: 2:00 PM - 5:00 PM (14:00 - 17:00)
            hours = time_obj.hour
            if hours >= 9 and hours < 14:
                period = 'morning'
            elif hours >= 14 and hours <= 17:
                period = 'afternoon'
            else:
                period = None
            
            cursor.execute('''
                INSERT INTO time_slots (time, label, date, available, period, location, created_at)
                VALUES (?, ?, ?, 1, ?, ?, CURRENT_TIMESTAMP)
            ''', (time, label, date, period, location))
            conn.commit()
            return True
    
    async def update_time_slot_availability(self, slot_id: int, available: bool) -> bool:
        """Update time slot availability"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE time_slots 
                SET available = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (available, slot_id))
            conn.commit()
            return cursor.rowcount > 0
    
    async def verify_applicant_coordinator(self, appointment_id: int, verified: bool) -> bool:
        """Mark attendance (present/absent) for an applicant by coordinator"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE appointments 
                SET coordinator_verified = ?, 
                    coordinator_verified_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (1 if verified else 0, 1 if verified else 0, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
    
    async def approve_applicant_coordinator(self, appointment_id: int, approved: bool) -> bool:
        """Approve or disapprove an applicant by coordinator"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE appointments 
                SET coordinator_approved = ?, 
                    coordinator_approved_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (1 if approved else 0, 1 if approved else 0, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
    
    async def get_verified_appointments(self) -> List[Dict[str, Any]]:
        """Get all appointments with attendance checked (for coordinator view)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, applicant_name, applicant_email, applicant_phone, 
                       scheduled_date, scheduled_time, status, notes, 
                       selected_song, additional_song, additional_song_singer,
                       coordinator_verified, coordinator_verified_at,
                       coordinator_approved, coordinator_approved_at,
                       final_decision, decision_made_at,
                       created_at, updated_at
                FROM appointments 
                WHERE coordinator_verified = 1
                ORDER BY scheduled_date ASC, scheduled_time ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_present_and_approved_appointments(self) -> List[Dict[str, Any]]:
        """Get appointments that are present (attendance checked) AND approved by coordinator (for judges)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, applicant_name, applicant_email, applicant_phone, 
                       scheduled_date, scheduled_time, status, notes, 
                       selected_song, additional_song, additional_song_singer,
                       coordinator_verified, coordinator_verified_at,
                       coordinator_approved, coordinator_approved_at,
                       final_decision, decision_made_at,
                       created_at, updated_at
                FROM appointments 
                WHERE coordinator_verified = 1 AND coordinator_approved = 1
                ORDER BY scheduled_date ASC, scheduled_time ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    async def submit_evaluation(self, appointment_id: int, judge_name: str, 
                               criteria_name: str, rating: int, comments: str = "") -> bool:
        """Submit or update an evaluation rating from a judge"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if evaluation already exists
            cursor.execute('''
                SELECT id FROM interview_evaluations 
                WHERE appointment_id = ? AND judge_name = ? AND criteria_name = ?
            ''', (appointment_id, judge_name, criteria_name))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing evaluation
                cursor.execute('''
                    UPDATE interview_evaluations 
                    SET rating = ?, comments = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE appointment_id = ? AND judge_name = ? AND criteria_name = ?
                ''', (rating, comments, appointment_id, judge_name, criteria_name))
            else:
                # Insert new evaluation
                cursor.execute('''
                    INSERT INTO interview_evaluations 
                    (appointment_id, judge_name, criteria_name, rating, comments)
                    VALUES (?, ?, ?, ?, ?)
                ''', (appointment_id, judge_name, criteria_name, rating, comments))
            conn.commit()
            return True
    
    async def get_evaluations(self, appointment_id: int) -> List[Dict[str, Any]]:
        """Get all evaluations for an appointment"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT appointment_id, judge_name, criteria_name, rating, comments,
                       created_at, updated_at
                FROM interview_evaluations 
                WHERE appointment_id = ?
                ORDER BY judge_name, criteria_name
            ''', (appointment_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_evaluation_averages(self, appointment_id: int) -> Dict[str, float]:
        """Calculate average ratings for each criteria across all judges"""
        evaluations = await self.get_evaluations(appointment_id)
        criteria_ratings: Dict[str, List[int]] = {}
        
        for eval in evaluations:
            criteria = eval['criteria_name']
            if criteria not in criteria_ratings:
                criteria_ratings[criteria] = []
            criteria_ratings[criteria].append(eval['rating'])
        
        averages = {}
        for criteria, ratings in criteria_ratings.items():
            if ratings:
                averages[criteria] = sum(ratings) / len(ratings)
        
        return averages
    
    async def set_final_decision(self, appointment_id: int, decision: str) -> bool:
        """Set final decision (accepted/rejected) for an applicant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE appointments 
                SET final_decision = ?, 
                    decision_made_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (decision, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def close(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._connection_pool:
                conn.close()
            self._connection_pool.clear()
        logger.info("Database connection pool closed")

