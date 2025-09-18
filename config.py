import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Google Drive Configuration
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    # Google Sheets Configuration
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEET_RANGE = os.getenv('GOOGLE_SHEET_RANGE', 'A:F')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', './vocalist_screening.db')
    
    # Notification Configuration
    REVIEWER_TELEGRAM_CHAT_ID = os.getenv('REVIEWER_TELEGRAM_CHAT_ID')
    REVIEWER_EMAIL = os.getenv('REVIEWER_EMAIL')
    
    # Google API Credentials
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', './credentials.json')
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    # Scopes for Google APIs
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
