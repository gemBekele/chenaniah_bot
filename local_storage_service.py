import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiofiles

class LocalStorageService:
    def __init__(self):
        self.storage_dir = Path("audio_files")
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories by date for organization
        self.today_dir = self.storage_dir / datetime.now().strftime("%Y-%m-%d")
        self.today_dir.mkdir(exist_ok=True)
    
    async def upload_audio_file(self, file_data: bytes, filename: str, 
                              mime_type: str = 'audio/mpeg') -> str:
        """Upload audio file to local storage and return file path"""
        try:
            # Generate unique filename to avoid conflicts
            file_id = str(uuid.uuid4())
            file_extension = filename.split('.')[-1] if '.' in filename else 'mp3'
            unique_filename = f"{file_id}.{file_extension}"
            
            # Save file to local storage
            file_path = self.today_dir / unique_filename
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            # Return the file path for database storage
            return str(file_path.relative_to(self.storage_dir))
            
        except Exception as e:
            print(f"Error saving audio file locally: {e}")
            raise
    
    def get_file_url(self, file_path: str) -> str:
        """Generate a URL for accessing the file"""
        # For Render, we'll serve files through the main app
        # In production, you'd want to set up proper file serving
        base_url = os.getenv('BASE_URL', 'https://chenaniah-bot.onrender.com')
        return f"{base_url}/audio_files/{file_path}"
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        full_path = self.storage_dir / file_path
        return full_path.stat().st_size if full_path.exists() else 0
