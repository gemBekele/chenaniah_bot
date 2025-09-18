#!/usr/bin/env python3
"""
Update Google Sheet to use simple audio links that open in Google Drive
"""

import asyncio
from google_services import GoogleSheetsService

async def update_to_simple_audio():
    """Update the Google Sheet with simple audio link format"""
    
    print("🔄 Updating to Simple Audio Link Format")
    print("=" * 50)
    
    # The file ID from the existing submission
    file_id = '1OBDOsT6gf3fVi-yqVRuIW0mTgL3I0Ekv'
    
    # Create the simple Google Drive view link
    view_link = f"https://drive.google.com/file/d/{file_id}/view"
    
    print("📋 Updated Google Sheets Structure:")
    print("=" * 50)
    print("A: Name")
    print("B: Address")
    print("C: Phone Number")
    print("D: Telegram Link")
    print("E: Audio Link (Play)")
    print("F: Submitted At")
    print("G: Status")
    
    print(f"\n🎵 Audio Link Formula:")
    print("=" * 50)
    print(f'E2: =HYPERLINK("{view_link}", "🎵 Play Audio")')
    
    print(f"\n🔗 Direct Link for Testing:")
    print("=" * 50)
    print(f"Click here to test: {view_link}")
    
    print(f"\n✅ Benefits of This Approach:")
    print("=" * 50)
    print("• Simple and clean interface")
    print("• Opens Google Drive's built-in audio player")
    print("• Works on all devices (desktop, mobile, tablet)")
    print("• No complex setup required")
    print("• Reliable audio playback")
    print("• Easy to use for reviewers")
    
    print(f"\n📱 How It Works:")
    print("=" * 50)
    print("1. Click '🎵 Play Audio' in the Google Sheet")
    print("2. Opens Google Drive in a new tab")
    print("3. Audio plays in Google Drive's built-in player")
    print("4. Full audio controls (play, pause, seek, volume)")
    print("5. Works on any device with internet access")
    
    print(f"\n🎯 Next Steps:")
    print("=" * 50)
    print("1. Update your Google Sheet column headers")
    print("2. Copy the formula into cell E2")
    print("3. Test the audio link")
    print("4. All new submissions will use this format automatically")

if __name__ == "__main__":
    asyncio.run(update_to_simple_audio())
