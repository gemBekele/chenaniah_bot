import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config
from database import Database
from google_services import GoogleDriveService, GoogleSheetsService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class VocalistScreeningBot:
    def __init__(self):
        self.db = Database()
        self.drive_service = GoogleDriveService()
        self.sheets_service = GoogleSheetsService()
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Reset any existing state
        await self.db.reset_user_state(user_id)
        
        # Store basic user info
        await self.db.update_user_state(
            user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            state='collecting_name'
        )
        
        welcome_message = f"""
🎵 Welcome to Chenaniah Worship Ministry!

Hi {user.first_name}! We're excited that you're interested in joining our ministry.

To help us get to know you better, I'll need to collect some information:

1. Your full name
2. Your address
3. Your phone number
4. Your worship song sample

Let's begin! 

Please send me your **full name**:
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on current state"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Get current user state
        user_data = await self.db.get_user_state(user_id)
        if not user_data:
            await update.message.reply_text("Please start the process by sending /start")
            return
        
        current_state = user_data.get('state', 'idle')
        
        if current_state == 'collecting_name':
            await self.handle_name_input(update, text, user_id)
        elif current_state == 'collecting_address':
            await self.handle_address_input(update, text, user_id)
        elif current_state == 'collecting_phone':
            await self.handle_phone_input(update, text, user_id)
        else:
            await update.message.reply_text("Please start the process by sending /start")
    
    async def handle_name_input(self, update: Update, text: str, user_id: int):
        """Handle name input"""
        await self.db.update_user_state(user_id, name=text, state='collecting_address')
        
        await update.message.reply_text(
            f"Great! Thanks, {text}.\n\n"
            "Now please send me your **address**:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_address_input(self, update: Update, text: str, user_id: int):
        """Handle address input"""
        await self.db.update_user_state(user_id, address=text, state='collecting_phone')
        
        await update.message.reply_text(
            f"Perfect! Address recorded.\n\n"
            "Now please send me your **phone number**:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_phone_input(self, update: Update, text: str, user_id: int):
        """Handle phone input"""
        await self.db.update_user_state(user_id, phone=text, state='collecting_audio')
        
        await update.message.reply_text(
            f"Excellent! Phone number recorded.\n\n"
            "Now please send me your **worship song sample** (voice note or music file).\n\n"
            "You can either:\n"
            "• Record a worship song directly\n"
            "• Upload an audio file of you singing ( not more than 2MB in size )\n\n"
            "Please share a clear recording of you singing a worship song!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio file uploads"""
        user_id = update.effective_user.id
        
        # Get current user state
        user_data = await self.db.get_user_state(user_id)
        if not user_data or user_data.get('state') != 'collecting_audio':
            await update.message.reply_text("Please complete the previous steps first by sending /start")
            return
        
        # Get audio file
        audio = update.message.audio or update.message.voice
        if not audio:
            await update.message.reply_text("Please send an audio file or voice message.")
            return
        
        try:
            # Show processing message
            processing_msg = await update.message.reply_text("🔄 Processing your worship song...")
            
            # Get file from Telegram
            file = await context.bot.get_file(audio.file_id)
            file_data = await file.download_as_bytearray()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = user_data.get('username', 'user')
            filename = f"worship_sample_{username}_{timestamp}.mp3"
            
            # Upload to Google Drive
            file_id = await self.drive_service.upload_audio_file(
                file_data, filename, audio.mime_type or 'audio/mpeg'
            )
            
            # Create a viewable link for display
            audio_view_link = f"https://drive.google.com/file/d/{file_id}/view"
            
            # Update user state with audio info
            await self.db.update_user_state(
                user_id,
                audio_file_id=audio.file_id,
                audio_drive_link=file_id,  # Store file ID for Google Sheets
                state='ready_to_submit'
            )
            
            # Show confirmation and submit button
            keyboard = [
                [InlineKeyboardButton("✅ Submit ", callback_data="submit_application")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_application")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                f"✅ Song processed successfully!\n\n"
                f"**Your Information:**\n"
                f"Name: {user_data.get('name')}\n"
                f"Address: {user_data.get('address')}\n"
                f"Phone: {user_data.get('phone')}\n"
                f"Worship Sample: [Preview Audio]({audio_view_link})\n\n"
                f"Click 'Submit to Ministry' to complete your application:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your audio file. Please try again."
            )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "submit_application":
            await self.submit_application(query, user_id)
        elif data == "cancel_application":
            await self.cancel_application(query, user_id)
    
    async def submit_application(self, query, user_id: int):
        """Submit the application"""
        try:
            # Get user data
            user_data = await self.db.get_user_state(user_id)
            if not user_data or user_data.get('state') != 'ready_to_submit':
                await query.edit_message_text("❌ No application data found. Please start over with /start")
                return
            
            # Create submission in database
            submission_id = await self.db.create_submission(
                user_id=user_id,
                name=user_data.get('name'),
                address=user_data.get('address'),
                phone=user_data.get('phone'),
                telegram_username=user_data.get('username'),
                audio_drive_link=user_data.get('audio_drive_link')
            )
            
            # Add to Google Sheets
            await self.sheets_service.add_submission(
                name=user_data.get('name'),
                address=user_data.get('address'),
                phone=user_data.get('phone'),
                telegram_username=user_data.get('username'),
                audio_link=user_data.get('audio_drive_link')
            )
            
            # Reset user state
            await self.db.reset_user_state(user_id)
            
            # Send confirmation
            await query.edit_message_text(
                f"🎉 **Application Submitted Successfully!**\n\n"
                f"Thank you, {user_data.get('name')}! Your worship ministry application has been submitted.\n\n"
                f"Our team will review your submission and contact you! \n\n"
                f"**Application ID:** #{submission_id}\n"
                f"**Submitted at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"May God bless your heart for worship! 🙏",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Notify reviewers (if configured)
            await self.notify_reviewers(user_data, submission_id)
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            await query.edit_message_text(
                "❌ Sorry, there was an error submitting your application. Please try again later."
            )
    
    async def cancel_application(self, query, user_id: int):
        """Cancel the application"""
        await self.db.reset_user_state(user_id)
        await query.edit_message_text(
            "❌ Application cancelled. Send /start to begin again anytime."
        )
    
    async def notify_reviewers(self, user_data: dict, submission_id: int):
        """Notify reviewers about new submission"""
        if not Config.REVIEWER_TELEGRAM_CHAT_ID:
            return
        
        try:
            notification_text = f"""
🔔 **New Vocalist Submission**

**Name:** {user_data.get('name')}
**Phone:** {user_data.get('phone')}
**Address:** {user_data.get('address')}
**Telegram:** @{user_data.get('username', 'No username')}
**Submission ID:** #{submission_id}
**Audio Link:** {user_data.get('audio_drive_link')}

Check the Google Sheet for full details.
            """
            
            # This would require the bot to send to reviewers
            # For now, we'll just log it
            logger.info(f"New submission notification: {notification_text}")
            
        except Exception as e:
            logger.error(f"Error notifying reviewers: {e}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🎵 **Chenaniah Worship Ministry Application Help**

**Commands:**
/start - Begin the application process
/help - Show this help message
/status - Check your application status

**How it works:**
1. Send /start to begin
2. Provide your name, address, and phone number
3. Upload your worship song sample
4. Submit your application to the ministry

**Requirements:**
- Clear recording of you leading worship or singing
- Valid contact information
- Complete all steps in order

**About Chenaniah Worship Ministry:**
We are seeking passionate worship leaders and singers to join our ministry team. We believe in the power of worship to draw people closer to God.

Need help? Contact our ministry team.
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        user_data = await self.db.get_user_state(user_id)
        
        if not user_data or user_data.get('state') == 'idle':
            await update.message.reply_text(
                "You don't have any active applications. Send /start to begin your worship ministry application."
            )
            return
        
        state = user_data.get('state', 'idle')
        status_messages = {
            'collecting_name': "⏳ Please provide your full name",
            'collecting_address': "⏳ Please provide your address",
            'collecting_phone': "⏳ Please provide your phone number",
            'collecting_audio': "⏳ Please upload your worship song sample",
            'ready_to_submit': "✅ Ready to submit - click the button in your last message"
        }
        
        message = status_messages.get(state, "Unknown status")
        await update.message.reply_text(message)
    
    def run(self):
        """Run the bot"""
        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Start the bot
        logger.info("Starting Vocalist Screening Bot...")
        self.application.run_polling()

if __name__ == "__main__":
    bot = VocalistScreeningBot()
    bot.run()
