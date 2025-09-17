#!/usr/bin/env python3
"""
Setup script for Google Service Account (Alternative to OAuth)
This is more suitable for bot applications.
"""

import json
import os
from pathlib import Path

def create_service_account_instructions():
    """Print instructions for creating a service account"""
    print("🔧 Setting up Google Service Account (Recommended for Bots)")
    print("=" * 60)
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. Select your project: chenaniah")
    print()
    print("3. Go to 'APIs & Services' → 'Credentials'")
    print()
    print("4. Click 'Create Credentials' → 'Service Account'")
    print()
    print("5. Fill in the details:")
    print("   - Service account name: vocalist-bot-service")
    print("   - Service account ID: vocalist-bot-service")
    print("   - Description: Service account for vocalist screening bot")
    print()
    print("6. Click 'Create and Continue'")
    print()
    print("7. Skip the 'Grant access' step (click 'Continue')")
    print()
    print("8. Click 'Done'")
    print()
    print("9. Find your service account in the list and click on it")
    print()
    print("10. Go to 'Keys' tab")
    print()
    print("11. Click 'Add Key' → 'Create new key'")
    print()
    print("12. Choose 'JSON' format and click 'Create'")
    print()
    print("13. Download the JSON file and save it as 'service_account.json'")
    print()
    print("14. Share your Google Drive folder and Google Sheet with the service account email")
    print("    (The email will be in the downloaded JSON file)")
    print()
    print("15. Update your .env file to use the service account:")
    print("    GOOGLE_CREDENTIALS_FILE=./service_account.json")
    print()

def update_google_services_for_service_account():
    """Update google_services.py to support service account"""
    
    service_account_code = '''
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API using service account"""
        try:
            # Try service account first
            if os.path.exists('service_account.json'):
                self.credentials = service_account.Credentials.from_service_account_file(
                    'service_account.json',
                    scopes=Config.GOOGLE_SCOPES
                )
                self.service = build('drive', 'v3', credentials=self.credentials)
                print("✅ Authenticated with service account")
                return
        except Exception as e:
            print(f"Service account authentication failed: {e}")
        
        # Fallback to OAuth (original code)
        creds = None
        token_file = 'token.json'
        
        if os.path.exists(token_file):
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(token_file, Config.GOOGLE_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(f"Google credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
                
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CREDENTIALS_FILE, Config.GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('drive', 'v3', credentials=creds)

class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            # Try service account first
            if os.path.exists('service_account.json'):
                self.credentials = service_account.Credentials.from_service_account_file(
                    'service_account.json',
                    scopes=Config.GOOGLE_SCOPES
                )
                self.service = build('sheets', 'v4', credentials=self.credentials)
                print("✅ Authenticated with service account")
                return
        except Exception as e:
            print(f"Service account authentication failed: {e}")
        
        # Fallback to OAuth (original code)
        creds = None
        token_file = 'token.json'
        
        if os.path.exists(token_file):
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(token_file, Config.GOOGLE_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(f"Google credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
                
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CREDENTIALS_FILE, Config.GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('sheets', 'v4', credentials=creds)
'''
    
    print("📝 Service account code prepared")
    print("This will be integrated into google_services.py")

if __name__ == "__main__":
    create_service_account_instructions()
    print("\n" + "=" * 60)
    print("Would you like to proceed with service account setup?")
    print("This is the recommended approach for bot applications.")
