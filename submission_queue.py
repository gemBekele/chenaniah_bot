import asyncio
import logging
from datetime import datetime
from queue import Queue, PriorityQueue
from threading import Thread
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Priority levels for submissions"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

@dataclass(order=True)
class QueuedSubmission:
    """Represents a queued submission with priority"""
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    user_id: int = field(compare=False)
    data: Dict[str, Any] = field(compare=False)
    retry_count: int = field(default=0, compare=False)
    
class SubmissionQueue:
    """
    Async submission queue to handle bursts and prevent database overload.
    Processes submissions in order with retry logic and rate limiting.
    """
    
    def __init__(self, max_workers: int = 5, max_queue_size: int = 1000):
        self.queue = PriorityQueue(maxsize=max_queue_size)
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.workers = []
        self.is_running = False
        self.processed_count = 0
        self.failed_count = 0
        self.retry_queue = Queue()
        
        # Stats tracking
        self.stats = {
            'total_queued': 0,
            'total_processed': 0,
            'total_failed': 0,
            'current_queue_size': 0,
            'average_processing_time': 0,
            'last_processed_at': None
        }
        
        logger.info(f"Initialized submission queue with {max_workers} workers")
    
    async def enqueue(self, user_id: int, data: Dict[str, Any], 
                     priority: Priority = Priority.NORMAL) -> bool:
        """
        Add a submission to the queue
        
        Args:
            user_id: Telegram user ID
            data: Submission data (name, address, phone, church, audio_file_path, etc.)
            priority: Priority level
            
        Returns:
            True if successfully queued, False if queue is full
        """
        try:
            if self.queue.full():
                logger.warning(f"Queue is full ({self.max_queue_size}), rejecting submission from user {user_id}")
                return False
            
            submission = QueuedSubmission(
                priority=priority.value,
                timestamp=datetime.now().timestamp(),
                user_id=user_id,
                data=data
            )
            
            self.queue.put(submission)
            self.stats['total_queued'] += 1
            self.stats['current_queue_size'] = self.queue.qsize()
            
            logger.info(f"Queued submission from user {user_id}, queue size: {self.queue.qsize()}")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing submission: {e}")
            return False
    
    async def process_submission(self, submission: QueuedSubmission, db) -> bool:
        """
        Process a single submission
        
        Args:
            submission: QueuedSubmission object
            db: Database instance
            
        Returns:
            True if successful, False otherwise
        """
        start_time = datetime.now()
        
        try:
            data = submission.data
            
            # Create submission in database
            submission_id = await db.create_submission(
                user_id=submission.user_id,
                name=data['name'],
                address=data['address'],
                phone=data['phone'],
                church=data['church'],
                telegram_username=data.get('telegram_username', ''),
                audio_file_path=data['audio_file_path'],
                audio_file_size=data.get('audio_file_size', 0),
                audio_duration=data.get('audio_duration', 0)
            )
            
            # Increment rate limit
            await db.increment_rate_limit(submission.user_id)
            
            # Update stats
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['total_processed'] += 1
            self.stats['last_processed_at'] = datetime.now().isoformat()
            
            # Update average processing time
            if self.stats['average_processing_time'] == 0:
                self.stats['average_processing_time'] = processing_time
            else:
                self.stats['average_processing_time'] = (
                    self.stats['average_processing_time'] * 0.9 + processing_time * 0.1
                )
            
            logger.info(
                f"Successfully processed submission {submission_id} for user {submission.user_id} "
                f"in {processing_time:.2f}s"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error processing submission for user {submission.user_id}: {e}")
            self.stats['total_failed'] += 1
            
            # Retry logic
            if submission.retry_count < 3:
                submission.retry_count += 1
                self.retry_queue.put(submission)
                logger.info(f"Queued submission for retry (attempt {submission.retry_count})")
            else:
                logger.error(f"Max retries exceeded for submission from user {submission.user_id}")
            
            return False
    
    async def worker(self, worker_id: int, db):
        """
        Worker coroutine that processes submissions from the queue
        
        Args:
            worker_id: Worker identifier
            db: Database instance
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get submission from queue with timeout
                if not self.queue.empty():
                    submission = self.queue.get(timeout=1)
                    
                    logger.debug(f"Worker {worker_id} processing submission from user {submission.user_id}")
                    
                    success = await self.process_submission(submission, db)
                    
                    if success:
                        self.processed_count += 1
                    else:
                        self.failed_count += 1
                    
                    self.queue.task_done()
                    self.stats['current_queue_size'] = self.queue.qsize()
                else:
                    # No items in queue, sleep briefly
                    await asyncio.sleep(0.5)
                
                # Process retry queue
                if not self.retry_queue.empty():
                    retry_submission = self.retry_queue.get()
                    # Add small delay before retry
                    await asyncio.sleep(2)
                    self.queue.put(retry_submission)
                    logger.info(f"Re-queued submission from user {retry_submission.user_id}")
                    
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self, db):
        """
        Start the queue workers
        
        Args:
            db: Database instance
        """
        if self.is_running:
            logger.warning("Queue is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting {self.max_workers} queue workers...")
        
        # Create worker tasks
        for i in range(self.max_workers):
            task = asyncio.create_task(self.worker(i, db))
            self.workers.append(task)
        
        logger.info("Submission queue started successfully")
    
    async def stop(self, wait_for_completion: bool = True):
        """
        Stop the queue workers
        
        Args:
            wait_for_completion: If True, wait for queue to be empty before stopping
        """
        logger.info("Stopping submission queue...")
        
        if wait_for_completion:
            logger.info(f"Waiting for {self.queue.qsize()} remaining submissions to complete...")
            await self.queue.join()
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Submission queue stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            **self.stats,
            'current_queue_size': self.queue.qsize(),
            'retry_queue_size': self.retry_queue.qsize(),
            'is_running': self.is_running,
            'workers': self.max_workers
        }
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def is_queue_full(self) -> bool:
        """Check if queue is full"""
        return self.queue.full()
    
    def get_queue_capacity(self) -> float:
        """Get queue capacity percentage"""
        return (self.queue.qsize() / self.max_queue_size) * 100

