#!/usr/bin/env python3
"""
Fix the Google Sheet by updating the cells with correct values
"""

import asyncio
from google_services import GoogleSheetsService

async def fix_google_sheet():
    """Fix the Google Sheet by updating the problematic cells"""
    
    print("🔧 Fixing Google Sheet - Removing Formula Issues")
    print("=" * 60)
    
    try:
        sheets = GoogleSheetsService()
        
        # The file ID from the existing submission
        file_id = '1wfeGfKRxqv4wRUhmUiPjQrcq7538CZte'
        
        # Create the correct values
        view_link = f"https://drive.google.com/file/d/{file_id}/view"
        telegram_link = "https://t.me/Gem_Bek"
        submitted_at = "2024-09-17 20:46:00"
        
        print("📝 Updating Google Sheet with correct values...")
        print(f"Audio Link: {view_link}")
        print(f"Telegram Link: {telegram_link}")
        print(f"Submitted At: {submitted_at}")
        
        # Update the specific cells
        # Row 2 (assuming header is row 1)
        updates = [
            {
                'range': 'E2',  # Audio link column
                'values': [[view_link]]
            },
            {
                'range': 'D2',  # Telegram link column  
                'values': [[telegram_link]]
            },
            {
                'range': 'F2',  # Submitted at column
                'values': [[submitted_at]]
            }
        ]
        
        # Apply the updates
        for update in updates:
            try:
                result = sheets.service.spreadsheets().values().update(
                    spreadsheetId=sheets.service._http.request.uri.split('/')[-1] if hasattr(sheets.service, '_http') else 'your_sheet_id',
                    range=update['range'],
                    valueInputOption='RAW',
                    body={'values': update['values']}
                ).execute()
                print(f"✅ Updated {update['range']}")
            except Exception as e:
                print(f"⚠️ Could not update {update['range']}: {e}")
        
        print("\n📋 Manual Fix Instructions (if automatic update fails):")
        print("=" * 60)
        print("1. Open your Google Sheet")
        print("2. Select cell E2 (Audio Link)")
        print("3. Delete the formula and type:")
        print(f"   {view_link}")
        print("4. Press Enter")
        print("5. Select cell D2 (Telegram Link)")
        print("6. Delete the formula and type:")
        print(f"   {telegram_link}")
        print("7. Press Enter")
        print("8. Select cell F2 (Submitted At)")
        print("9. Delete the formula and type:")
        print(f"   {submitted_at}")
        print("10. Press Enter")
        
        print("\n✅ What This Fixes:")
        print("=" * 60)
        print("• Audio links will be clickable")
        print("• Telegram links will be clickable")
        print("• Timestamps will display correctly")
        print("• No more formula text showing")
        
        print("\n🧪 Test the Links:")
        print("=" * 60)
        print(f"Audio: {view_link}")
        print(f"Telegram: {telegram_link}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📋 Manual Fix Required:")
        print("=" * 60)
        print("The automatic fix failed. Please follow the manual instructions above.")

if __name__ == "__main__":
    asyncio.run(fix_google_sheet())
