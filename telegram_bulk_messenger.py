#!/usr/bin/env python3
"""
Safe Telegram Bulk Messaging Utility
Respects Telegram's rate limits:
- 1 message per second per chat
- 30 messages per second across all chats
- 20 messages per minute per group
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from telegram import Bot
from config import Config
from database_optimized import DatabaseOptimized
import time

logger = logging.getLogger(__name__)

class TelegramBulkMessenger:
    """
    Safe bulk messaging utility that respects Telegram rate limits.
    
    Rate Limits (as of 2024):
    - 1 message per second per chat
    - 30 messages per second across all chats
    - 20 messages per minute per group
    
    This utility implements conservative limits:
    - 0.5 messages per second per chat (2 second delay)
    - 20 messages per second across all chats (safety margin)
    """
    
    def __init__(self):
        self.bot = None
        if Config.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        else:
            logger.warning("Telegram bot token not configured")
        
        self.db = DatabaseOptimized()
        
        # Conservative rate limits (safety margin below Telegram's limits)
        self.MIN_DELAY_BETWEEN_MESSAGES = 2.0  # 2 seconds between messages (0.5 msg/sec)
        self.MAX_MESSAGES_PER_SECOND = 20  # 20 messages/sec across all chats
        self.MAX_MESSAGES_PER_MINUTE = 50  # Conservative limit
        
        # Tracking
        self.messages_sent_this_minute = 0
        self.minute_start_time = time.time()
        self.last_message_times = {}  # Track last message time per chat_id
    
    async def send_message_safe(self, chat_id: int, message: str, 
                                parse_mode: str = 'Markdown') -> tuple[bool, Optional[str]]:
        """
        Send a single message with rate limiting protection.
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        if not self.bot:
            return False, "Bot not initialized"
        
        # Check per-chat rate limit (1 msg per second per chat)
        if chat_id in self.last_message_times:
            time_since_last = time.time() - self.last_message_times[chat_id]
            if time_since_last < self.MIN_DELAY_BETWEEN_MESSAGES:
                wait_time = self.MIN_DELAY_BETWEEN_MESSAGES - time_since_last
                await asyncio.sleep(wait_time)
        
        # Check per-minute limit
        current_time = time.time()
        if current_time - self.minute_start_time >= 60:
            # Reset minute counter
            self.messages_sent_this_minute = 0
            self.minute_start_time = current_time
        
        if self.messages_sent_this_minute >= self.MAX_MESSAGES_PER_MINUTE:
            # Wait until next minute
            wait_time = 60 - (current_time - self.minute_start_time)
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
                self.messages_sent_this_minute = 0
                self.minute_start_time = time.time()
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
            )
            
            # Update tracking
            self.last_message_times[chat_id] = time.time()
            self.messages_sent_this_minute += 1
            
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle rate limit errors (429)
            if "429" in error_msg or "Too Many Requests" in error_msg:
                logger.warning(f"Rate limit hit for chat {chat_id}. Waiting 60 seconds...")
                await asyncio.sleep(60)
                # Retry once
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=parse_mode
                    )
                    self.last_message_times[chat_id] = time.time()
                    self.messages_sent_this_minute += 1
                    return True, None
                except Exception as retry_error:
                    return False, f"Retry failed: {str(retry_error)}"
            
            return False, error_msg
    
    async def send_to_applicants(self, message: str, 
                                status_filter: Optional[str] = None,
                                limit: Optional[int] = None,
                                dry_run: bool = False) -> Dict[str, Any]:
        """
        Send message to applicants from database.
        
        Args:
            message: Message to send
            status_filter: Optional status filter ('approved', 'rejected', 'pending')
            limit: Optional limit on number of recipients
            dry_run: If True, don't send, just return list of recipients
        
        Returns:
            Dict with success count, failed count, and details
        """
        if not self.bot:
            return {
                'success': False,
                'error': 'Bot not initialized',
                'sent': 0,
                'failed': 0,
                'total': 0
            }
        
        # Get applicants from database
        submissions = await self.db.get_all_submissions(
            status=status_filter,
            limit=limit or 10000,
            offset=0
        )
        
        # Filter to only those with user_id (chat_id)
        recipients = [
            s for s in submissions 
            if s.get('user_id') and s.get('user_id') is not None
        ]
        
        if limit:
            recipients = recipients[:limit]
        
        total = len(recipients)
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'total': total,
                'recipients': [
                    {
                        'id': r['id'],
                        'name': r['name'],
                        'user_id': r['user_id'],
                        'status': r.get('status', 'unknown')
                    }
                    for r in recipients
                ]
            }
        
        logger.info(f"Starting bulk message to {total} applicants...")
        
        sent = 0
        failed = 0
        errors = []
        
        for i, submission in enumerate(recipients, 1):
            user_id = submission['user_id']
            name = submission.get('name', 'Applicant')
            
            logger.info(f"[{i}/{total}] Sending to {name} (user_id: {user_id})...")
            
            success, error = await self.send_message_safe(user_id, message)
            
            if success:
                sent += 1
                logger.info(f"✅ Sent to {name}")
            else:
                failed += 1
                error_detail = {
                    'name': name,
                    'user_id': user_id,
                    'error': error
                }
                errors.append(error_detail)
                logger.error(f"❌ Failed to send to {name}: {error}")
            
            # Small delay between messages (additional safety)
            if i < total:
                await asyncio.sleep(0.1)
        
        result = {
            'success': True,
            'total': total,
            'sent': sent,
            'failed': failed,
            'errors': errors[:10] if errors else []  # Limit error details
        }
        
        if len(errors) > 10:
            result['error_note'] = f"({len(errors) - 10} more errors not shown)"
        
        logger.info(f"Bulk messaging complete: {sent} sent, {failed} failed")
        return result
    
    async def send_to_applicants_by_ids(self, user_ids: List[int], 
                                       message: str) -> Dict[str, Any]:
        """
        Send message to specific user IDs.
        
        Args:
            user_ids: List of Telegram user IDs (chat IDs)
            message: Message to send
        
        Returns:
            Dict with success count, failed count, and details
        """
        if not self.bot:
            return {
                'success': False,
                'error': 'Bot not initialized',
                'sent': 0,
                'failed': 0,
                'total': 0
            }
        
        total = len(user_ids)
        sent = 0
        failed = 0
        errors = []
        
        logger.info(f"Sending message to {total} users...")
        
        for i, user_id in enumerate(user_ids, 1):
            logger.info(f"[{i}/{total}] Sending to user_id: {user_id}...")
            
            success, error = await self.send_message_safe(user_id, message)
            
            if success:
                sent += 1
            else:
                failed += 1
                errors.append({'user_id': user_id, 'error': error})
                logger.error(f"Failed to send to user_id {user_id}: {error}")
            
            if i < total:
                await asyncio.sleep(0.1)
        
        return {
            'success': True,
            'total': total,
            'sent': sent,
            'failed': failed,
            'errors': errors[:10]
        }


async def main():
    """CLI for bulk messaging"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send bulk messages to applicants via Telegram')
    parser.add_argument('message', help='Message to send')
    parser.add_argument('--status', choices=['pending', 'approved', 'rejected'],
                       help='Filter by application status')
    parser.add_argument('--limit', type=int, help='Limit number of recipients')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show recipients without sending')
    parser.add_argument('--user-ids', nargs='+', type=int,
                       help='Send to specific user IDs instead of querying database')
    
    args = parser.parse_args()
    
    messenger = TelegramBulkMessenger()
    
    if args.user_ids:
        result = await messenger.send_to_applicants_by_ids(args.user_ids, args.message)
    else:
        result = await messenger.send_to_applicants(
            args.message,
            status_filter=args.status,
            limit=args.limit,
            dry_run=args.dry_run
        )
    
    print("\n" + "="*50)
    print("Bulk Messaging Results:")
    print("="*50)
    print(f"Total: {result['total']}")
    print(f"Sent: {result['sent']}")
    print(f"Failed: {result['failed']}")
    
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('dry_run'):
        print("\nRecipients (dry run):")
        for recipient in result['recipients']:
            print(f"  - {recipient['name']} (ID: {recipient['user_id']}, Status: {recipient['status']})")


if __name__ == '__main__':
    asyncio.run(main())

