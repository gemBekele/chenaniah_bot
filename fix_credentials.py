#!/usr/bin/env python3
"""
Script to help fix Google credentials issues for production deployment
"""

import json
import os
import sys
from pathlib import Path

def check_environment_variables():
    """Check what environment variables are currently set"""
    print("🔍 Checking Environment Variables")
    print("=" * 50)
    
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        print("📁 Found .env file")
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if 'SERVICE_ACCOUNT' in key or 'CREDENTIALS' in key:
                        print(f"  {key}: {'*' * 20} (hidden)")
                    else:
                        print(f"  {key}: {value}")
    else:
        print("❌ No .env file found")
    
    print()
    
    # Check environment variables
    google_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GOOGLE_DRIVE_FOLDER_ID', 
        'GOOGLE_SHEET_ID',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'GOOGLE_CREDENTIALS_FILE'
    ]
    
    print("🌍 Environment Variables:")
    for var in google_vars:
        value = os.getenv(var)
        if value:
            if 'SERVICE_ACCOUNT' in var or 'CREDENTIALS' in var:
                print(f"  ✅ {var}: Set (hidden)")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    print()

def validate_service_account_json():
    """Validate the service account JSON format"""
    print("🔍 Validating Service Account JSON")
    print("=" * 50)
    
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")
        return False
    
    try:
        # Parse the JSON
        data = json.loads(service_account_json)
        print("✅ JSON is valid")
        
        # Check required fields
        required_fields = {
            'type': 'service_account',
            'project_id': 'string',
            'private_key_id': 'string', 
            'private_key': 'string',
            'client_email': 'string',
            'client_id': 'string',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': 'string'
        }
        
        print("\n📋 Field Validation:")
        all_valid = True
        for field, expected in required_fields.items():
            if field in data:
                if field in ['auth_uri', 'token_uri']:
                    if data[field] == expected:
                        print(f"  ✅ {field}: {data[field]}")
                    else:
                        print(f"  ⚠️  {field}: {data[field]} (expected: {expected})")
                else:
                    value = str(data[field])
                    if len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: Missing")
                all_valid = False
        
        if all_valid:
            print("\n🎉 Service account JSON is properly formatted!")
            return True
        else:
            print("\n❌ Service account JSON is missing required fields")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        print("\n💡 Common issues:")
        print("  - JSON is not properly escaped")
        print("  - Missing quotes around strings")
        print("  - Contains line breaks (should be on one line)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_sample_env_file():
    """Create a sample .env file with proper format"""
    print("\n📝 Creating Sample .env File")
    print("=" * 50)
    
    sample_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Google Drive Configuration  
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Google Sheets Configuration
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_SHEET_RANGE=A:F

# Database Configuration
DATABASE_PATH=./vocalist_screening.db

# Notification Configuration (Optional)
REVIEWER_TELEGRAM_CHAT_ID=your_chat_id_here
REVIEWER_EMAIL=reviewer@example.com

# Google API Credentials (Choose ONE method)
# Method 1: Service Account JSON (Recommended for production)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project","private_key_id":"key-id","private_key":"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n","client_email":"your-service@project.iam.gserviceaccount.com","client_id":"client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service%40project.iam.gserviceaccount.com"}

# Method 2: OAuth Credentials File (Alternative)
# GOOGLE_CREDENTIALS_FILE=./credentials.json
"""
    
    with open('.env.sample', 'w') as f:
        f.write(sample_content)
    
    print("✅ Created .env.sample file")
    print("📋 Copy this to .env and fill in your actual values")

def show_render_setup_instructions():
    """Show instructions for setting up credentials in Render"""
    print("\n🚀 Render.com Setup Instructions")
    print("=" * 50)
    print()
    print("1. Go to your Render service dashboard")
    print("2. Navigate to Environment tab")
    print("3. Add these environment variables:")
    print()
    print("   TELEGRAM_BOT_TOKEN=your_bot_token")
    print("   GOOGLE_DRIVE_FOLDER_ID=your_folder_id")
    print("   GOOGLE_SHEET_ID=your_sheet_id")
    print("   GOOGLE_SERVICE_ACCOUNT_JSON={\"type\":\"service_account\",...}")
    print()
    print("4. For GOOGLE_SERVICE_ACCOUNT_JSON:")
    print("   - Get your service account JSON from Google Cloud Console")
    print("   - Copy the ENTIRE JSON content")
    print("   - Paste it as the value (all on one line)")
    print("   - Make sure to escape quotes properly")
    print()
    print("5. Save and redeploy your service")

def main():
    """Main function"""
    print("🔧 Google Credentials Fix Tool")
    print("=" * 50)
    print()
    
    # Check current setup
    check_environment_variables()
    
    # Validate service account JSON if set
    service_account_valid = validate_service_account_json()
    
    # Create sample files
    create_sample_env_file()
    
    # Show Render setup instructions
    show_render_setup_instructions()
    
    print("\n📋 Summary:")
    print("=" * 50)
    if service_account_valid:
        print("✅ Your service account JSON is properly formatted!")
        print("🚀 You can deploy to Render.com now.")
    else:
        print("❌ Service account JSON needs to be fixed")
        print("📝 Follow the instructions above to set up proper credentials")
    
    print("\n💡 Quick Fix:")
    print("1. Run: python setup_service_account.py")
    print("2. Follow the Google Cloud Console setup")
    print("3. Copy the JSON to Render environment variables")
    print("4. Redeploy your service")

if __name__ == "__main__":
    main()
