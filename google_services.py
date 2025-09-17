import os
import io
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from config import Config

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            # Try service account first (recommended for bots)
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
        
        # Fallback to OAuth
        creds = None
        token_file = 'token.json'
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, Config.GOOGLE_SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(f"Google credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CREDENTIALS_FILE, Config.GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('drive', 'v3', credentials=creds)
    
    async def upload_audio_file(self, file_data: bytes, filename: str, 
                              mime_type: str = 'audio/mpeg') -> str:
        """Upload audio file to Google Drive and return shareable link"""
        try:
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [Config.GOOGLE_DRIVE_FOLDER_ID]
            }
            
            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(file_data),
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink,webContentLink'
            ).execute()
            
            # Make file publicly viewable
            self.service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            
            # Return the file ID for flexible link generation
            file_id = file['id']
            
            # Return the file ID so we can create different link types
            return file_id
            
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
            raise

class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try service account first (recommended for bots)
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
        
        # Fallback to OAuth
        creds = None
        token_file = 'token.json'
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, Config.GOOGLE_SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(f"Google credentials file not found: {Config.GOOGLE_CREDENTIALS_FILE}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CREDENTIALS_FILE, Config.GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.credentials = creds
        self.service = build('sheets', 'v4', credentials=creds)
    
    async def add_submission(self, name: str, address: str, phone: str, 
                           telegram_username: str, audio_link: str) -> None:
        """Add a new submission to Google Sheets"""
        try:
            from datetime import datetime
            
            # audio_link is now the file ID directly
            file_id = audio_link
            
            # Create multiple link formats for better usability
            play_link = f"https://drive.google.com/uc?export=download&id={file_id}"
            view_link = f"https://drive.google.com/file/d/{file_id}/view"
            embed_link = f"https://drive.google.com/file/d/{file_id}/preview"
            
            # Create a simple, clean audio link that opens in Google Drive player
            # The preview link opens Google Drive's built-in audio player
            audio_cell_value = f"=HYPERLINK(\"{embed_link}\", \"🎵 Play Audio\")"
            
            # Prepare row data with multiple audio access options
            values = [
                [
                    name,
                    address,
                    phone,
                    f"https://t.me/{telegram_username}" if telegram_username else "No username",
                    audio_cell_value,  # Main audio link
                    f"=HYPERLINK(\"{play_link}\", \"📥 Download\")",  # Download link
                    f"=HYPERLINK(\"{view_link}\", \"👁️ View\")",  # View link
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Pending"  # Status column
                ]
            ]
            
            # Append to sheet
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=Config.GOOGLE_SHEET_RANGE,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"Added submission to Google Sheets: {result.get('updates', {}).get('updatedRows', 0)} rows added")
            
        except Exception as e:
            print(f"Error adding to Google Sheets: {e}")
            raise
    
    async def get_submissions(self) -> list:
        """Get all submissions from Google Sheets"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=Config.GOOGLE_SHEET_ID,
                range=Config.GOOGLE_SHEET_RANGE
            ).execute()
            
            values = result.get('values', [])
            return values
            
        except Exception as e:
            print(f"Error getting submissions from Google Sheets: {e}")
            raise
