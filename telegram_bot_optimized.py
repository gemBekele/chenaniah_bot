import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config
from database_optimized import DatabaseOptimized
from local_storage_service import LocalStorageService
from submission_queue import SubmissionQueue, Priority
from performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VocalistScreeningBotOptimized:
    """Optimized bot with rate limiting, queuing, and performance monitoring"""
    
    def __init__(self):
        self.db = DatabaseOptimized(pool_size=10)
        self.storage_service = LocalStorageService()
        self.submission_queue = SubmissionQueue(max_workers=5, max_queue_size=1000)
        self.performance_monitor = PerformanceMonitor(check_interval=30)
        self.application = None
        
        # Configuration
        self.MAX_SUBMISSIONS_PER_DAY = 3
        self.MAX_AUDIO_SIZE_MB = 5
        self.MAX_AUDIO_SIZE_BYTES = self.MAX_AUDIO_SIZE_MB * 1024 * 1024
        
        logger.info("Optimized bot initialized with queue and monitoring")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        # Check rate limit
        can_submit, message = await self.db.check_rate_limit(user_id, self.MAX_SUBMISSIONS_PER_DAY)
        
        if not can_submit:
            await update.message.reply_text(
                f"❌ {message}\n\n"
                f"You can only submit {self.MAX_SUBMISSIONS_PER_DAY} applications per day.\n"
                f"እባክዎ በቀን {self.MAX_SUBMISSIONS_PER_DAY} ጊዜ ብቻ ማስገባት ይችላሉ።",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
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
            🎵 **Welcome to Chenaniah music Ministry!**
            ክናንያ የህብረት መዘምራን

            Hi {user.first_name}! We're excited that you're interested in joining our ministry.
            እንኳን ወደ ክናንያ የህብረት መዘምራን መመዝገብያ በደህና መጡ

            To help us get to know you better, We'll need to collect some information:
            እባክዎ ሙሉ ስምዎትን ይንገሩን

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
            "Now please send us your **address**:\n"
            "የመኖርያ አድራሻዎን ይንገሩን",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_address_input(self, update: Update, text: str, user_id: int):
        """Handle address input"""
        await self.db.update_user_state(user_id, address=text, state='collecting_phone')
        
        await update.message.reply_text(
            f"Perfect! Address recorded.\n\n"
            "Now please send us your **phone number**:\n"
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
        
        # Check file size
        file_size = audio.file_size
        if file_size > self.MAX_AUDIO_SIZE_BYTES:
            await update.message.reply_text(
                f"❌ Audio file is too large ({file_size / (1024*1024):.1f} MB).\n"
                f"Maximum size is {self.MAX_AUDIO_SIZE_MB} MB.\n\n"
                f"❌ የድምፅ ፋይሉ በጣም ትልቅ ነው።\n"
                f"ከፍተኛው መጠን {self.MAX_AUDIO_SIZE_MB} MB ነው።"
            )
            return
        
        # Check queue capacity
        if self.submission_queue.get_queue_capacity() > 90:
            await update.message.reply_text(
                "⚠️ System is experiencing high load. Please try again in a few minutes.\n"
                "⚠️ እባክዎ በጥቂት ደቂቃዎች ውስጥ እንደገና ይሞክሩ።"
            )
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
            
            # Determine file extension
            mime_type = audio.mime_type or 'audio/mpeg'
            if 'ogg' in mime_type or 'opus' in mime_type:
                extension = 'ogg'
            elif 'wav' in mime_type:
                extension = 'wav'
            else:
                extension = 'mp3'
            
            filename = f"worship_sample_{username}_{timestamp}.{extension}"
            
            # Upload to local storage
            file_path = await self.storage_service.upload_audio_file(
                file_data, filename, mime_type
            )
            
            # Create viewable link
            audio_view_link = self.storage_service.get_file_url(file_path)
            
            # Get audio duration
            audio_duration = getattr(audio, 'duration', 0)
            
            # Update user state with audio info
            await self.db.update_user_state(
                user_id,
                audio_file_id=audio.file_id,
                audio_file_path=file_path,
                file_size=file_size,
                audio_duration=audio_duration,
                state='ready_to_submit'
            )
            
            # Show confirmation and submit button
            keyboard = [
                [InlineKeyboardButton("✅ Submit ", callback_data="submit_application")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_application")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(
                f"**Your Information:**\n"
                f"**የእርስዎ መረጃ:**\n"
                f"Name: {user_data.get('name')}\n"
                f"Address: {user_data.get('address')}\n"
                f"Phone: {user_data.get('phone')}\n"
                f"Church: {user_data.get('church')}\n"
                f"Worship Sample: [Preview Audio]({audio_view_link})\n\n"
                f"Click 'Submit' to complete your application:\n"
                f" ለማጠናቀቅ 'Submit' ይጫኑ:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error uploading audio: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error uploading your audio file. Please try again.\n"
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
        """Submit the application to queue"""
        try:
            # Get user data
            user_data = await self.db.get_user_state(user_id)
            if not user_data or user_data.get('state') != 'ready_to_submit':
                await query.edit_message_text("❌ No application data found. Please start over with /start")
                return
            
            # Check rate limit again
            can_submit, message = await self.db.check_rate_limit(user_id, self.MAX_SUBMISSIONS_PER_DAY)
            if not can_submit:
                await query.edit_message_text(f"❌ {message}")
                return
            
            # Prepare submission data
            submission_data = {
                'name': user_data.get('name'),
                'address': user_data.get('address'),
                'phone': user_data.get('phone'),
                'church': user_data.get('church'),
                'telegram_username': user_data.get('username', ''),
                'audio_file_path': user_data.get('audio_file_path'),
                'audio_file_size': user_data.get('file_size', 0),
                'audio_duration': user_data.get('audio_duration', 0)
            }
            
            # Add to queue
            queued = await self.submission_queue.enqueue(
                user_id, submission_data, Priority.NORMAL
            )
            
            if not queued:
                await query.edit_message_text(
                    "⚠️ System is at capacity. Please try again in a few minutes.\n"
                    "⚠️ ስርዓቱ በሙሉ አቅሙ ላይ ነው። እባክዎ በጥቂት ደቂቃዎች ውስጥ እንደገና ይሞክሩ።"
                )
                return
            
            # Reset user state
            await self.db.reset_user_state(user_id)
            
            # Get queue position
            queue_position = self.submission_queue.get_queue_size()
            
            # Send confirmation
            await query.edit_message_text(
                f"🎉 **Application Recieved Successfully!**\n\n"
                f"Thank you, {user_data.get('name')}! Your application is being processed.\n"
                f"Our team will review your submission and contact you!\n\n"
                f"**Submitted at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"May God bless you! 🙏\n",
                parse_mode=ParseMode.MARKDOWN
            )
            
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
            f"Maximum file size: {self.MAX_AUDIO_SIZE_MB} MB\n\n"
            "Please share a clear recording of you singing a worship song!",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system statistics (admin only)"""
        # Simple admin check - you can enhance this
        user_id = update.effective_user.id
        
        # Get stats
        queue_stats = self.submission_queue.get_stats()
        performance_stats = self.performance_monitor.get_current_metrics()
        db_stats = await self.db.get_submission_stats()
        
        stats_message = f"""
📊 **System Statistics**

**Queue Status:**
• Current queue size: {queue_stats['current_queue_size']}
• Total processed: {queue_stats['total_processed']}
• Total failed: {queue_stats['total_failed']}
• Avg processing time: {queue_stats['average_processing_time']:.2f}s

**Database:**
• Total submissions: {db_stats['total']}
• Pending: {db_stats['pending']}
• Approved: {db_stats['approved']}
• Rejected: {db_stats['rejected']}
        """
        
        if performance_stats:
            stats_message += f"""
**System Performance:**
• CPU: {performance_stats['cpu_percent']:.1f}%
• Memory: {performance_stats['memory_percent']:.1f}%
• Available RAM: {performance_stats['memory_available_mb']:.0f} MB
• Bot Memory: {performance_stats['bot_memory_mb']:.1f} MB
            """
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🎵 **Chenaniah Music Ministry Application Help**
ክናንያ የህብረት መዘምራን አመልካች እርዳታ

**Commands:**
/start - Begin the application process
/help - Show this help message
/stats - Show system statistics

**How it works:**
1. Send /start to begin
2. Provide your name, address, and phone number
3. Upload your worship song sample
4. Submit your application to the ministry

**Requirements:**
- Clear recording of you leading worship or singing
- Valid contact information
- Complete all steps in order

Need help? Contact our ministry team.
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
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
        
        # Start queue and monitoring
        loop = asyncio.get_event_loop()
        loop.create_task(self.submission_queue.start(self.db))
        loop.create_task(self.performance_monitor.start(self.submission_queue))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        self.application.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Start the bot
        logger.info("Starting Optimized Vocalist Screening Bot...")
        try:
            self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            # Cleanup
            loop.run_until_complete(self.submission_queue.stop())
            loop.run_until_complete(self.performance_monitor.stop())
            self.db.close()

if __name__ == "__main__":
    bot = VocalistScreeningBotOptimized()
    bot.run()

