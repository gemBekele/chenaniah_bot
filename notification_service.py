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
🔔 **New Worship Ministry Application**

**Name:** {submission_data.get('name', 'N/A')}
**Phone:** {submission_data.get('phone', 'N/A')}
**Address:** {submission_data.get('address', 'N/A')}
**Telegram:** @{submission_data.get('telegram_username', 'No username')}
**Application ID:** #{submission_data.get('id', 'N/A')}
**Worship Sample:** {submission_data.get('audio_drive_link', 'N/A')}
**Submitted:** {submission_data.get('submitted_at', 'N/A')}

Please prayerfully review this application in the Google Sheet.
        """
    
    async def notify_reviewers_status_update(self, submission_id: int, status: str, 
                                           reviewer_comments: str = None) -> bool:
        """Send notification about status update"""
        if not self.bot or not Config.REVIEWER_TELEGRAM_CHAT_ID:
            return False
        
        try:
            message = f"""
📝 **Application Status Updated**

**Application ID:** #{submission_id}
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
📊 **Daily Ministry Application Summary**

**Total Applications Today:** {submissions_count}
**Pending Review:** {pending_count}

Please review applications in the Google Sheet.
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
    
    async def notify_applicant_status_update(self, user_id: int, name: str, status: str, 
                                           reviewer_comments: str = None) -> bool:
        """Send status update notification to applicant via Telegram"""
        if not self.bot:
            logger.warning("Notification service not configured - missing bot token")
            return False
        
        if not user_id:
            logger.warning(f"Cannot send notification - no user_id provided for applicant {name}")
            return False
        
        try:
            # Format message based on status
            if status == 'approved':
                message = f"""🎉 **Congratulations, {name}!**

Your worship ministry application has been **approved**!

We are excited to have you join our ministry. You will be contacted soon with further details.

May God bless you! 🙏"""
            elif status == 'rejected':
                message = f"""Dear {name},

Thank you for your interest in our worship ministry. After careful prayerful consideration, your application was not approved at this time.

We encourage you to continue growing in your musical gifts and consider applying again in the future.

Blessings! 🙏"""
            else:
                # For other status updates (e.g., pending -> reviewed)
                message = f"""Dear {name},

Your application status has been updated to: **{status}**

"""
                if reviewer_comments:
                    message += f"**Note:** {reviewer_comments}\n"
                message += "\nBlessings! 🙏"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Status update notification sent to applicant {name} (user_id: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update notification to applicant {name} (user_id: {user_id}): {e}")
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
