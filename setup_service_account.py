#!/usr/bin/env python3
"""
Script to help set up Google service account for production deployment
"""

import json
import os

def create_service_account_instructions():
    """Print step-by-step instructions for creating a service account"""
    print("🔧 Google Service Account Setup Instructions")
    print("=" * 60)
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com")
    print()
    print("2. Select your project (or create a new one)")
    print()
    print("3. Enable required APIs:")
    print("   - Go to APIs & Services → Library")
    print("   - Search for 'Google Drive API' → Enable")
    print("   - Search for 'Google Sheets API' → Enable")
    print()
    print("4. Create Service Account:")
    print("   - Go to APIs & Services → Credentials")
    print("   - Click 'Create Credentials' → 'Service Account'")
    print("   - Fill in name: 'vocalist-bot-service'")
    print("   - Click 'Create and Continue'")
    print("   - Skip role assignment for now")
    print("   - Click 'Done'")
    print()
    print("5. Create Service Account Key:")
    print("   - Click on the created service account")
    print("   - Go to 'Keys' tab")
    print("   - Click 'Add Key' → 'Create new key'")
    print("   - Select 'JSON' format")
    print("   - Click 'Create'")
    print("   - Download the JSON file")
    print()
    print("6. Set up Google Drive folder:")
    print("   - Create a folder in Google Drive")
    print("   - Right-click → Share")
    print("   - Add the service account email (from the JSON file)")
    print("   - Give 'Editor' permissions")
    print("   - Copy the folder ID from the URL")
    print()
    print("7. Set up Google Sheet:")
    print("   - Create a new Google Sheet")
    print("   - Right-click → Share")
    print("   - Add the service account email")
    print("   - Give 'Editor' permissions")
    print("   - Copy the sheet ID from the URL")
    print()
    print("8. Set Environment Variables in Render:")
    print("   - Go to your Render service dashboard")
    print("   - Go to Environment tab")
    print("   - Add these variables:")
    print()
    print("   TELEGRAM_BOT_TOKEN=your_bot_token")
    print("   GOOGLE_DRIVE_FOLDER_ID=your_folder_id")
    print("   GOOGLE_SHEET_ID=your_sheet_id")
    print("   GOOGLE_SERVICE_ACCOUNT_JSON={\"type\":\"service_account\",...}")
    print()
    print("   For GOOGLE_SERVICE_ACCOUNT_JSON:")
    print("   - Open the downloaded JSON file")
    print("   - Copy the entire content")
    print("   - Paste it as the value (all on one line)")
    print()

def format_json_for_env(json_file_path):
    """Format JSON file for environment variable"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to single-line JSON string
        json_string = json.dumps(data, separators=(',', ':'))
        
        print("📋 Formatted JSON for environment variable:")
        print("=" * 60)
        print("GOOGLE_SERVICE_ACCOUNT_JSON=" + json_string)
        print()
        print("Copy the above line and paste it as an environment variable in Render.")
        
        return json_string
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {json_file_path}")
        return None

def validate_json_structure(json_file_path):
    """Validate the structure of the service account JSON"""
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri',
            'auth_provider_x509_cert_url', 'client_x509_cert_url'
        ]
        
        print("🔍 Validating service account JSON structure...")
        print("=" * 60)
        
        missing_fields = []
        for field in required_fields:
            if field in data:
                print(f"✅ {field}: {data[field][:50]}..." if len(str(data[field])) > 50 else f"✅ {field}: {data[field]}")
            else:
                print(f"❌ {field}: Missing")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"\n❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        else:
            print("\n✅ All required fields are present!")
            return True
            
    except FileNotFoundError:
        print(f"❌ File not found: {json_file_path}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {json_file_path}")
        return False

def main():
    """Main function"""
    print("🚀 Google Service Account Setup Helper")
    print("=" * 60)
    print()
    
    # Check if JSON file exists
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and 'service' in f.lower()]
    
    if json_files:
        print(f"📁 Found JSON files: {', '.join(json_files)}")
        print()
        
        for json_file in json_files:
            print(f"🔍 Checking {json_file}...")
            if validate_json_structure(json_file):
                print(f"\n📋 Formatting {json_file} for environment variable...")
                format_json_for_env(json_file)
                break
    else:
        print("📁 No service account JSON files found in current directory")
        print()
        create_service_account_instructions()

if __name__ == "__main__":
    main()