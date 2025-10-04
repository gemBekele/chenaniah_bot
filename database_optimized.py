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
    
    async def get_all_submissions(self, status: str = None, limit: int = 100, offset: int = 0) -> list:
        """Get all submissions with optional status filter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM submissions 
                    WHERE status = ?
                    ORDER BY submitted_at DESC
                    LIMIT ? OFFSET ?
                ''', (status, limit, offset))
            else:
                cursor.execute('''
                    SELECT * FROM submissions 
                    ORDER BY submitted_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
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
    
    def close(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._connection_pool:
                conn.close()
            self._connection_pool.clear()
        logger.info("Database connection pool closed")

