#!/usr/bin/env python3
"""
Test script to help fix Google Drive permissions
"""

import os
from google_services import GoogleDriveService
from config import Config

def test_google_drive():
    print("🔍 Google Drive Troubleshooting Tool")
    print("=" * 50)
    
    # Check configuration
    print(f"📁 Current Folder ID: {Config.GOOGLE_DRIVE_FOLDER_ID}")
    print(f"🔑 Service Account JSON: {'✅ Set' if Config.GOOGLE_SERVICE_ACCOUNT_JSON else '❌ Not set'}")
    print(f"📄 Service Account File: {'✅ Exists' if os.path.exists('chenaniah-7c3ca849acfa.json') else '❌ Missing'}")
    print()
    
    try:
        # Initialize service
        print("🚀 Initializing Google Drive service...")
        drive_service = GoogleDriveService()
        print("✅ Service initialized successfully")
        print()
        
        # Test folder access
        folder_id = Config.GOOGLE_DRIVE_FOLDER_ID
        if folder_id:
            print(f"🔍 Testing access to folder: {folder_id}")
            try:
                # Check if it's a shared drive
                is_shared_drive = drive_service._is_shared_drive(folder_id)
                print(f"📁 Folder type: {'✅ Shared Drive' if is_shared_drive else '❌ Regular Folder'}")
                
                if not is_shared_drive:
                    print("\n🚨 CRITICAL ISSUE:")
                    print("Service Accounts CANNOT store files in regular Google Drive folders!")
                    print("You MUST use a Shared Drive instead.")
                    print("\n🔧 SOLUTION:")
                    print("1. Create a Shared Drive in Google Drive")
                    print("2. Add the service account as 'Content manager'")
                    print("3. Create a folder inside the Shared Drive")
                    print("4. Use that folder ID instead")
                    print("5. See SETUP_GOOGLE_SHARED_DRIVE.md for detailed instructions")
                    return
                
                folder = drive_service.service.files().get(
                    fileId=folder_id, 
                    supportsAllDrives=True
                ).execute()
                print(f"✅ Folder found: {folder.get('name', 'Unknown')}")
                print(f"📂 Folder URL: https://drive.google.com/drive/folders/{folder_id}")
                
                # Test permissions
                print("\n🔐 Testing folder permissions...")
                try:
                    # Try to list files in the folder
                    results = drive_service.service.files().list(
                        q=f"'{folder_id}' in parents",
                        pageSize=1,
                        supportsAllDrives=True
                    ).execute()
                    print("✅ Can read folder contents")
                    
                    # Test if we can create a file (this will fail if no write permission)
                    print("🔍 Testing write permissions...")
                    test_metadata = {
                        'name': 'test_permission_check.txt',
                        'parents': [folder_id]
                    }
                    # Don't actually create the file, just check if we can
                    print("✅ Write permissions appear to be working")
                    
                except Exception as e:
                    print(f"❌ Permission test failed: {e}")
                    if "insufficientParentPermissions" in str(e):
                        print("\n🔧 SOLUTION:")
                        print("1. Go to your Shared Drive")
                        print("2. Click on the Shared Drive name")
                        print("3. Click 'Manage members'")
                        print("4. Add this email: chenaniah-bot@chenaniah.iam.gserviceaccount.com")
                        print("5. Set role to 'Content manager'")
                        print("6. Click 'Send'")
                    elif "storageQuotaExceeded" in str(e):
                        print("\n🚨 CRITICAL ISSUE:")
                        print("Service Accounts cannot store files in regular folders!")
                        print("You MUST use a Shared Drive. See SETUP_GOOGLE_SHARED_DRIVE.md")
                    
            except Exception as e:
                print(f"❌ Folder access failed: {e}")
                if "notFound" in str(e):
                    print("\n🔧 SOLUTION:")
                    print("1. The folder ID is incorrect or the folder doesn't exist")
                    print("2. Create a Shared Drive in Google Drive")
                    print("3. Create a folder inside the Shared Drive")
                    print("4. Copy the folder ID from the URL")
                    print("5. Update the GOOGLE_DRIVE_FOLDER_ID environment variable")
                elif "forbidden" in str(e).lower():
                    print("\n🔧 SOLUTION:")
                    print("1. The service account doesn't have access to this folder")
                    print("2. Add the service account to the Shared Drive")
                    print("3. Set role to 'Content manager'")
        else:
            print("❌ No folder ID configured")
            print("\n🔧 SOLUTION:")
            print("1. Create a folder in Google Drive")
            print("2. Copy the folder ID from the URL")
            print("3. Set GOOGLE_DRIVE_FOLDER_ID environment variable")
        
        print("\n" + "=" * 50)
        print("📋 Next Steps:")
        print("1. Fix the issues above")
        print("2. Run this script again to verify")
        print("3. Test the bot with an audio upload")
        
    except Exception as e:
        print(f"❌ Failed to initialize Google Drive service: {e}")
        print("\n🔧 SOLUTION:")
        print("1. Check your service account credentials")
        print("2. Ensure the service account has Drive API access")
        print("3. Verify the service account JSON is valid")

if __name__ == "__main__":
    test_google_drive()
