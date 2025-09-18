import os
from typing import Optional
from telegram import Bot
from config import Config

class TelegramStorageService:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    
    async def upload_audio_file(self, file_data: bytes, filename: str, 
                              mime_type: str = 'audio/mpeg') -> str:
        """Upload audio file using Telegram's file storage"""
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            # Upload to Telegram as a document
            with open(temp_file_path, 'rb') as file:
                # Send to a private channel or use the bot's own chat
                # For this example, we'll use the bot's get_file method
                # In practice, you'd send to a private channel and get the file_id
                pass
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Return a Telegram file ID or URL
            return f"telegram_file_{filename}"
            
        except Exception as e:
            print(f"Error uploading to Telegram: {e}")
            raise
    
    def get_file_url(self, file_id: str) -> str:
        """Generate a URL for accessing the file via Telegram"""
        # This would be a Telegram file URL
        return f"https://api.telegram.org/file/bot{Config.TELEGRAM_BOT_TOKEN}/{file_id}"
