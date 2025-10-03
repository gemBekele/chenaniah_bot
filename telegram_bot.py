import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config
from database import Database
from local_storage_service import LocalStorageService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class VocalistScreeningBot:
    def __init__(self):
        self.db = Database()
        self.storage_service = LocalStorageService()
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
🎵 **Welcome to Chenaniah Worship Ministry!**
ክናንያ የህብረት መዘምራን

Hi {user.first_name}! We're excited that you're interested in joining our ministry.
እንኳን ወደ ክናንያ የህብረት መዘምራን መመዝገብያ በደህና መጡ

To help us get to know you better, I'll need to collect some information:
እባክዎ ሙሉ ስምዎትን ይንገሩን

**Information needed:**
1. Your full name
2. Your address  
3. Your phone number
4. Your local church
5. Your worship song sample

Let's begin! 

 **full name ሙሉ ስም**  :
        """
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on current state"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Get current user state
        user_data = await self.db.get_user_state(user_id)
        if not user_data:
            await update.message.reply_text("Please start the process by sending /start\nእባክዎ ሂደቱን ለመጀመር /start ይላኩ")
            return
        
        current_state = user_data.get('state', 'idle')
        
        if current_state == 'collecting_name':
            await self.handle_name_input(update, text, user_id)
        elif current_state == 'collecting_address':
            await self.handle_address_input(update, text, user_id)
        elif current_state == 'collecting_phone':
            await self.handle_phone_input(update, text, user_id)
        elif current_state == 'collecting_church':
            await self.handle_church_input(update, text, user_id)
        else:
            await update.message.reply_text("Please start the process by sending /start\nእባክዎ ሂደቱን ለመጀመር /start ይላኩ")
    
    async def handle_name_input(self, update: Update, text: str, user_id: int):
        """Handle name input"""
        await self.db.update_user_state(user_id, name=text, state='collecting_address')
        
        await update.message.reply_text(
            f"Great! Thanks, {text}.\n\n"
            "Now please send me your **address**:\n"
            "የመኖርያ አድራሻዎን ይንገሩን",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_address_input(self, update: Update, text: str, user_id: int):
        """Handle address input"""
        await self.db.update_user_state(user_id, address=text, state='collecting_phone')
        
        await update.message.reply_text(
            f"Perfect! Address recorded.\n\n"
            "Now please send me your **phone number**:\n"
            "መገኘት የሚችሉቡትን የስልክ ቁጥርዎን ያስገቡ",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_phone_input(self, update: Update, text: str, user_id: int):
        """Handle phone input"""
        await self.db.update_user_state(user_id, phone=text, state='collecting_church')
        
        await update.message.reply_text(
            f"Excellent! Phone number recorded.\n\n"
            "Now please tell us your **local church** (the church where you worship):\n"
            "ህብረት የሚያደርጉበትን ቤተክርስቲያን ያሳውቁን",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_church_input(self, update: Update, text: str, user_id: int):
        """Handle church input"""
        # Validate church name (at least 3 characters)
        if len(text.strip()) < 3:
            await update.message.reply_text(
                "❌ Please enter a valid church name (at least 3 characters).\n"
                "❌ እባክዎ ትክክለኛ የቤተክርስቲያን ስም ያስገቡ (ቢያንስ 3 ፊደላት)።",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await self.db.update_user_state(user_id, church=text, state='collecting_audio')
        
        await update.message.reply_text(
            f"Perfect! Church recorded.\n\n"
            "Now please send me your **worship song sample** (voice note or music file).\n"
            "ድምጽዎን ለመለየት እንዲጠቅመን እባክዎ እዚሁ በመዘመር የድምፅ መልዕክት ይላኩ\n\n"
            "You can either:\n"
            "• Record a worship song directly\n"
            "• Upload an audio file of you singing (not more than 2MB in size)\n\n"
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
            await update.message.reply_text("Please send an audio file or voice message.\nእባክዎ የድምፅ ፋይል ወይም የድምፅ መልዕክት ይላኩ።")
            return
        
        try:
            # Show processing message
            processing_msg = await update.message.reply_text("🔄 Processing your worship song......")
            
            # Get file from Telegram
            file = await context.bot.get_file(audio.file_id)
            file_data = await file.download_as_bytearray()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = user_data.get('username', 'user')
            filename = f"worship_sample_{username}_{timestamp}.mp3"
            
            # Upload to local storage
            file_path = await self.storage_service.upload_audio_file(
                file_data, filename, audio.mime_type or 'audio/mpeg'
            )
            # Create a viewable link for display
            audio_view_link = self.storage_service.get_file_url(file_path)
            
            # Get file size
            file_size = len(file_data)
            
            # Get audio duration (approximate from file size, or use actual duration if available)
            audio_duration = getattr(audio, 'duration', 0)
            
            # Update user state with audio info
            await self.db.update_user_state(
                user_id,
                audio_file_id=audio.file_id,
                audio_drive_link=file_path,  # Store file path for reference
                state='ready_to_submit'
            )
            
            # Show confirmation and submit button
            keyboard = [
                [InlineKeyboardButton("✅ Submit ", callback_data="submit_application")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_application")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                f"✅ Song processed successfully!\n"
                f"ድምፅ በተሳካ ሁኔታ ተሰርዟል!\n\n"
                f"**Your Information:**\n"
                f"**የእርስዎ መረጃ:**\n"
                f"Name: {user_data.get('name')}\n"
                f"Address: {user_data.get('address')}\n"
                f"Phone: {user_data.get('phone')}\n"
                f"Church: {user_data.get('church')}\n"
                f"Worship Sample: [Preview Audio]({audio_view_link})\n\n"
                f"Click 'Submit to Ministry' to complete your application:\n"
                f"አመልካችንን ለማጠናቀቅ 'Submit to Ministry' ይጫኑ:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error uploading audio to Google Drive: {e}")
            
            # Provide specific error messages based on the error type
            if "storageQuotaExceeded" in str(e) or "Service Accounts do not have storage quota" in str(e):
                error_message = (
                    "❌ **Google Drive Storage Error**\n"
                    "❌ **የጉግል ድራይቭ ማከማቻ ስህተት**\n\n"
                    "There's an issue with Google Drive storage. Please contact the administrator.\n"
                    "የጉግል ድራይቭ ማከማቻ ችግር አለ። እባክዎ አስተዳዳሪውን ያግኙ።\n\n"
                    "**Your audio file is required for the application.**\n"
                    "**የድምፅ ፋይልዎ ለአመልካቹ ያስፈልጋል።**"
                )
            elif "insufficientParentPermissions" in str(e):
                error_message = (
                    "❌ **Google Drive Permission Error**\n"
                    "❌ **የጉግል ድራይቭ ፈቃድ ስህተት**\n\n"
                    "The bot doesn't have permission to upload files. Please contact the administrator.\n"
                    "ቦቱ ፋይሎችን ለመላክ ፈቃድ የለውም። እባክዎ አስተዳዳሪውን ያግኙ።"
                )
            elif "HttpError 403" in str(e):
                error_message = (
                    "❌ **Google Drive Access Denied**\n"
                    "❌ **የጉግል ድራይቭ መድረሻ ተከልክሏል**\n\n"
                    "There's an issue with Google Drive access. Please contact the administrator.\n"
                    "የጉግል ድራይቭ መድረሻ ችግር አለ። እባክዎ አስተዳዳሪውን ያግኙ።"
                )
            else:
                error_message = (
                    "❌ Sorry, there was an error uploading your audio file. Please try again.\n"
                    "❌ ይቅርታ፣ የድምፅ ፋይልዎን በመላክ ላይ ስህተት ተከስቷል። እባክዎ እንደገና ይሞክሩ።\n\n"
                    "If the problem persists, please contact support.\n"
                    "ችግሩ ካለቀቀ እባክዎ ድጋፍ ያግኙ።"
                )
            
            # Show error message with retry option only
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="retry_audio")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                error_message + "\n\n**Please try uploading your audio file again:**\n**እባክዎ የድምፅ ፋይልዎን እንደገና ይላኩ:**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
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
        elif data == "retry_audio":
            await self.retry_audio(query, user_id)
    
    async def submit_application(self, query, user_id: int):
        """Submit the application"""
        try:
            # Get user data
            user_data = await self.db.get_user_state(user_id)
            if not user_data or user_data.get('state') != 'ready_to_submit':
                await query.edit_message_text("❌ No application data found. Please start over with /start")
                return
            
            # Get file size from stored path
            audio_file_path = user_data.get('audio_drive_link', '')
            file_size = self.storage_service.get_file_size(audio_file_path)
            
            # Create submission in database
            submission_id = await self.db.create_submission(
                user_id=user_id,
                name=user_data.get('name'),
                address=user_data.get('address'),
                phone=user_data.get('phone'),
                church=user_data.get('church'),
                telegram_username=user_data.get('username'),
                audio_file_path=audio_file_path,
                audio_file_size=file_size,
                audio_duration=0  # Will be calculated if needed
            )
            
            # Reset user state
            await self.db.reset_user_state(user_id)
            
            # Send confirmation
            await query.edit_message_text(
                f"🎉 **Application Submitted Successfully!**\n"
                f"Thank you, {user_data.get('name')}! Your worship ministry application has been submitted.\n"
                f"Our team will review your submission and contact you!\n"
                f"**Application ID:** #{submission_id}\n"
                f"**Submitted at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"May God bless you! 🙏\n",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Notify reviewers (if configured)
            await self.notify_reviewers(user_data, submission_id)
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            await query.edit_message_text(
                "❌ Sorry, there was an error submitting your application. Please try again later.\n"
            )
    
    async def cancel_application(self, query, user_id: int):
        """Cancel the application"""
        await self.db.reset_user_state(user_id)
        await query.edit_message_text(
            "❌ Application cancelled. Send /start to begin again anytime.\n"
        )
    
    async def retry_audio(self, query, user_id: int):
        """Retry audio upload"""
        await query.edit_message_text(
            "🔄 Please try uploading your worship song sample again.\n"
            "You can either:\n"
            "• Record a worship song directly\n"
            "• Upload an audio file of you singing (not more than 2MB in size)\n\n"
            "Please share a clear recording of you singing a worship song!",
            parse_mode=ParseMode.MARKDOWN
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
ክናንያ የህብረት መዘምራን አመልካች እርዳታ

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
                "You don't have any active applications. Send /start to begin your worship ministry application.\n"
            )
            return
        
        state = user_data.get('state', 'idle')
        status_messages = {
            'collecting_name': "⏳ Please provide your full name\nእባክዎ ሙሉ ስምዎትን ይንገሩን",
            'collecting_address': "⏳ Please provide your address\nየመኖርያ አድራሻዎን ይንገሩን",
            'collecting_phone': "⏳ Please provide your phone number\nለመገኘት የሚችሉቡትን የስልክ ቁጥርዎን ያስገቡ",
            'collecting_church': "⏳ Please provide your local church\nህብረት የሚያደርጉበትን ቤተክርስቲያን ያሳውቁን",
            'collecting_audio': "⏳ Please upload your worship song sample\nየህብረት ድምፅ ናሙናዎን እባክዎ ይላኩ",
            'ready_to_submit': "✅ Ready to submit - click the button in your last message\n✅ ለመላክ ዝግጁ - በመጨረሻው መልዕክትዎ ውስጥ ያለውን ቁልፍ ይጫኑ"
        }
        
        message = status_messages.get(state, "Unknown status")
        await update.message.reply_text(message)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Send user-friendly error message
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again or contact support if the issue persists.\n"
            )

    def run(self):
        """Run the bot"""
        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Start the bot
        logger.info("Starting Vocalist Screening Bot...")
        try:
            # Add a delay to prevent conflicts with other instances
            import time
            import random
            delay = random.uniform(1, 5)  # Random delay between 1-5 seconds
            logger.info(f"Waiting {delay:.2f} seconds to prevent conflicts...")
            time.sleep(delay)
            
            # The run_polling method already handles webhook cleanup
            self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise

if __name__ == "__main__":
    bot = VocalistScreeningBot()
    bot.run()
