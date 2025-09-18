#!/usr/bin/env python3
"""
Script to validate Google service account credentials
Run this locally to test your credentials before deploying
"""

import json
import os
from google.oauth2 import service_account
from config import Config

def validate_service_account_json():
    """Validate the service account JSON from environment variable"""
    print("🔍 Validating Google Service Account Credentials...")
    print("=" * 50)
    
    # Check if environment variable is set
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set")
        print("\nTo fix this:")
        print("1. Set the environment variable in Render.com")
        print("2. Or run: export GOOGLE_SERVICE_ACCOUNT_JSON='your_json_here'")
        return False
    
    try:
        # Parse the JSON
        service_account_info = json.loads(service_account_json)
        print("✅ JSON is valid")
        
        # Check required fields
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri',
            'auth_provider_x509_cert_url', 'client_x509_cert_url'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in service_account_info:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        print("✅ All required fields are present")
        
        # Try to create credentials
        try:
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=Config.GOOGLE_SCOPES
            )
            print("✅ Credentials created successfully")
            print(f"✅ Service account email: {service_account_info['client_email']}")
            print(f"✅ Project ID: {service_account_info['project_id']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create credentials: {e}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        print("\nMake sure the JSON is properly formatted and on one line")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def validate_credentials_file():
    """Validate credentials.json file"""
    print("\n🔍 Checking for credentials.json file...")
    print("=" * 50)
    
    credentials_file = Config.GOOGLE_CREDENTIALS_FILE
    if os.path.exists(credentials_file):
        print(f"✅ Found credentials file: {credentials_file}")
        return True
    else:
        print(f"❌ Credentials file not found: {credentials_file}")
        return False

def main():
    """Main validation function"""
    print("🚀 Google Credentials Validation Tool")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validate service account JSON
    service_account_valid = validate_service_account_json()
    
    # Validate credentials file
    credentials_file_valid = validate_credentials_file()
    
    print("\n📋 Summary:")
    print("=" * 50)
    print(f"Service Account JSON: {'✅ Valid' if service_account_valid else '❌ Invalid'}")
    print(f"Credentials File: {'✅ Found' if credentials_file_valid else '❌ Not Found'}")
    
    if service_account_valid:
        print("\n🎉 Your service account is properly configured!")
        print("You can deploy to Render.com now.")
    elif credentials_file_valid:
        print("\n⚠️  Using OAuth credentials file (less secure for production)")
        print("Consider setting up a service account for better security.")
    else:
        print("\n❌ No valid credentials found!")
        print("Please set up either:")
        print("1. GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
        print("2. credentials.json file")
    
    return service_account_valid or credentials_file_valid

if __name__ == "__main__":
    main()
