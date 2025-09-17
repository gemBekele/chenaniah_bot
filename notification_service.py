import asyncio
import logging
from typing import Dict, Any, Optional
from telegram import Bot
from config import Config

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.bot = None
        if Config.TELEGRAM_BOT_TOKEN:
            self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    
    async def notify_reviewers_new_submission(self, submission_data: Dict[str, Any]) -> bool:
        """Send notification to reviewers about new submission"""
        if not self.bot or not Config.REVIEWER_TELEGRAM_CHAT_ID:
            logger.warning("Notification service not configured - missing bot token or reviewer chat ID")
            return False
        
        try:
            message = self._format_submission_notification(submission_data)
            
            await self.bot.send_message(
                chat_id=Config.REVIEWER_TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Notification sent to reviewers for submission #{submission_data.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _format_submission_notification(self, submission_data: Dict[str, Any]) -> str:
        """Format submission data into notification message"""
        return f"""
🔔 **New Vocalist Submission**

**Name:** {submission_data.get('name', 'N/A')}
**Phone:** {submission_data.get('phone', 'N/A')}
**Address:** {submission_data.get('address', 'N/A')}
**Telegram:** @{submission_data.get('telegram_username', 'No username')}
**Submission ID:** #{submission_data.get('id', 'N/A')}
**Audio Link:** {submission_data.get('audio_drive_link', 'N/A')}
**Submitted:** {submission_data.get('submitted_at', 'N/A')}

Check the Google Sheet for full details and to add your review.
        """
    
    async def notify_reviewers_status_update(self, submission_id: int, status: str, 
                                           reviewer_comments: str = None) -> bool:
        """Send notification about status update"""
        if not self.bot or not Config.REVIEWER_TELEGRAM_CHAT_ID:
            return False
        
        try:
            message = f"""
📝 **Submission Status Updated**

**Submission ID:** #{submission_id}
**New Status:** {status}
"""
            if reviewer_comments:
                message += f"**Comments:** {reviewer_comments}\n"
            
            await self.bot.send_message(
                chat_id=Config.REVIEWER_TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update notification: {e}")
            return False
    
    async def send_daily_summary(self, submissions_count: int, pending_count: int) -> bool:
        """Send daily summary to reviewers"""
        if not self.bot or not Config.REVIEWER_TELEGRAM_CHAT_ID:
            return False
        
        try:
            message = f"""
📊 **Daily Submission Summary**

**Total Submissions Today:** {submissions_count}
**Pending Review:** {pending_count}

Check the Google Sheet for details.
            """
            
            await self.bot.send_message(
                chat_id=Config.REVIEWER_TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False

# Email notification service (optional)
class EmailNotificationService:
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = 587
        self.email = None
        self.password = None
    
    async def send_submission_notification(self, submission_data: Dict[str, Any]) -> bool:
        """Send email notification about new submission"""
        # This would require additional email configuration
        # For now, just log the notification
        logger.info(f"Email notification would be sent for submission #{submission_data.get('id')}")
        return True
