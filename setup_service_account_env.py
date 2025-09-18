#!/usr/bin/env python3
"""
Helper script to set up Google Service Account credentials for Render deployment
"""

import json
import os
from pathlib import Path

def setup_service_account_instructions():
    """Print instructions for setting up service account"""
    print("🔐 Google Service Account Setup for Render Deployment")
    print("=" * 60)
    print()
    print("1. Go to Google Cloud Console: https://console.cloud.google.com")
    print("2. Select your project (or create a new one)")
    print("3. Navigate to: APIs & Services → Credentials")
    print("4. Click 'Create Credentials' → 'Service Account'")
    print("5. Fill in the service account details:")
    print("   - Name: vocalist-screening-bot")
    print("   - Description: Service account for vocalist screening bot")
    print("6. Click 'Create and Continue'")
    print("7. Skip role assignment for now, click 'Continue'")
    print("8. Click 'Done'")
    print("9. Click on the created service account")
    print("10. Go to 'Keys' tab → 'Add Key' → 'Create new key' → 'JSON'")
    print("11. Download the JSON file")
    print("12. Copy the entire JSON content")
    print("13. In Render dashboard, add environment variable:")
    print("    Key: GOOGLE_SERVICE_ACCOUNT_JSON")
    print("    Value: [paste the entire JSON content here]")
    print()
    print("14. Make sure these APIs are enabled:")
    print("    - Google Drive API")
    print("    - Google Sheets API")
    print()
    print("15. Share your Google Drive folder and Google Sheet with the service account email")
    print("    (found in the 'client_email' field of the JSON)")
    print()

def validate_service_account_json():
    """Validate if service account JSON is properly formatted"""
    json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not json_str:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
        return False
    
    try:
        service_account_info = json.loads(json_str)
        
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [field for field in required_fields if field not in service_account_info]
        
        if missing_fields:
            print(f"❌ Missing required fields in service account JSON: {missing_fields}")
            return False
        
        if service_account_info.get('type') != 'service_account':
            print("❌ Invalid service account type")
            return False
        
        print("✅ Service account JSON is valid")
        print(f"   Project ID: {service_account_info.get('project_id')}")
        print(f"   Client Email: {service_account_info.get('client_email')}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating service account: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Vocalist Screening Bot - Service Account Setup")
    print()
    
    # Check if running in production (Render)
    if os.getenv('RENDER'):
        print("🌐 Running on Render - checking service account configuration...")
        print()
        
        if validate_service_account_json():
            print("✅ Service account is properly configured!")
        else:
            print("❌ Service account configuration is invalid")
            print("Please follow the setup instructions below:")
            print()
            setup_service_account_instructions()
    else:
        print("💻 Running locally - showing setup instructions...")
        print()
        setup_service_account_instructions()
        
        # Check if service account file exists locally
        if Path('service_account.json').exists():
            print("✅ Found service_account.json file locally")
            print("You can use this for local development")
        else:
            print("ℹ️  No service_account.json found locally")
            print("This is normal for production deployment")

if __name__ == "__main__":
    main()
