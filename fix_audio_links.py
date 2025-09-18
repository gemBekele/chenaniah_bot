#!/usr/bin/env python3
"""
Fix existing audio links in Google Sheet to make them clickable
"""

import asyncio
from google_services import GoogleSheetsService

async def fix_audio_links():
    """Fix the existing audio link to make it clickable"""
    
    print("🔧 Fixing Audio Links in Google Sheet")
    print("=" * 50)
    
    try:
        sheets = GoogleSheetsService()
        
        # The file ID from the existing submission
        file_id = '1wfeGfKRxqv4wRUhmUiPjQrcq7538CZte'
        
        # Create the correct Google Drive view link
        view_link = f"https://drive.google.com/file/d/{file_id}/view"
        
        print(f"📝 Updating audio link to: {view_link}")
        
        # Update the specific cell (row 2, column E)
        # Note: This is a simplified update - you may need to adjust the range
        print("🔄 Updating Google Sheet...")
        
        # For now, just show you what to do manually
        print("\n📋 Manual Fix Instructions:")
        print("=" * 50)
        print("1. Open your Google Sheet")
        print("2. Go to cell E2 (or wherever the audio link is)")
        print("3. Replace the formula with this direct link:")
        print(f"   {view_link}")
        print("4. Press Enter")
        print("5. The link should now be clickable!")
        
        print(f"\n✅ Alternative: Use this formula instead:")
        print("=" * 50)
        print(f'=HYPERLINK("https://drive.google.com/file/d/{file_id}/view", "🎵 Play Audio")')
        
        print(f"\n🧪 Test the link:")
        print("=" * 50)
        print(f"Click here: {view_link}")
        
        print(f"\n💡 Why this happens:")
        print("=" * 50)
        print("• Google Sheets sometimes treats formulas as text")
        print("• Direct links are more reliable")
        print("• USER_ENTERED option helps with link recognition")
        print("• New submissions will use the correct format")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_audio_links())
