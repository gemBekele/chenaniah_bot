#!/usr/bin/env python3
"""
Setup script for Vocalist Screening Bot
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print("✅ Python version check passed")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "temp", "exports"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment_file():
    """Setup environment file"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("✅ Created .env file from template")
            print("⚠️  Please edit .env file with your actual configuration values")
        else:
            print("❌ env.example file not found")
    else:
        print("✅ .env file already exists")

def setup_google_credentials():
    """Setup Google API credentials"""
    creds_file = Path("credentials.json")
    if not creds_file.exists():
        print("⚠️  Google credentials.json file not found")
        print("Please download your Google API credentials and save as 'credentials.json'")
        print("Instructions:")
        print("1. Go to Google Cloud Console")
        print("2. Create a new project or select existing")
        print("3. Enable Google Drive API and Google Sheets API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the JSON file and rename to 'credentials.json'")
    else:
        print("✅ Google credentials file found")

def setup_telegram_bot():
    """Setup Telegram bot token"""
    print("🤖 Telegram Bot Setup:")
    print("1. Message @BotFather on Telegram")
    print("2. Create a new bot with /newbot")
    print("3. Copy the bot token")
    print("4. Add the token to your .env file as TELEGRAM_BOT_TOKEN")

def setup_google_drive():
    """Setup Google Drive folder"""
    print("📁 Google Drive Setup:")
    print("1. Create a folder in Google Drive for audio files")
    print("2. Right-click the folder and select 'Share'")
    print("3. Make it accessible to anyone with the link")
    print("4. Copy the folder ID from the URL")
    print("5. Add the folder ID to your .env file as GOOGLE_DRIVE_FOLDER_ID")

def setup_google_sheets():
    """Setup Google Sheets"""
    print("📊 Google Sheets Setup:")
    print("1. Create a new Google Sheet")
    print("2. Add these column headers in row 1:")
    print("   Name | Address | Phone Number | Telegram Link | Audio Link | Submitted At | Status")
    print("3. Copy the sheet ID from the URL")
    print("4. Add the sheet ID to your .env file as GOOGLE_SHEET_ID")
    print("5. Set GOOGLE_SHEET_RANGE to A:G (or adjust based on your columns)")

def create_sample_google_sheet():
    """Create a sample Google Sheet structure"""
    sample_sheet = {
        "headers": [
            "Name",
            "Address", 
            "Phone Number",
            "Telegram Link",
            "Audio Link",
            "Submitted At",
            "Status",
            "Reviewer Comments"
        ],
        "sample_data": [
            [
                "John Doe",
                "123 Main St, City, Country",
                "+1234567890",
                "https://t.me/johndoe",
                "https://drive.google.com/file/d/...",
                "2024-01-15 10:30:00",
                "Pending",
                ""
            ]
        ]
    }
    
    with open("sample_sheet_structure.json", "w") as f:
        json.dump(sample_sheet, f, indent=2)
    
    print("✅ Created sample_sheet_structure.json for reference")

def main():
    """Main setup function"""
    print("🎤 Vocalist Screening Bot Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup environment file
    setup_environment_file()
    
    # Setup Google credentials
    setup_google_credentials()
    
    # Create sample sheet structure
    create_sample_google_sheet()
    
    # Print setup instructions
    print("\n" + "=" * 40)
    print("📋 Next Steps:")
    print("=" * 40)
    
    setup_telegram_bot()
    print()
    setup_google_drive()
    print()
    setup_google_sheets()
    print()
    
    print("🔧 Configuration:")
    print("1. Edit .env file with your actual values")
    print("2. Place credentials.json in the project root")
    print("3. Run: python telegram_bot.py")
    print()
    print("📚 For detailed instructions, see README.md")
    print("✅ Setup complete!")

if __name__ == "__main__":
    main()
