#!/usr/bin/env python3
"""
Update Google Sheet with better audio link formats
"""

import asyncio
from google_services import GoogleSheetsService

async def update_sheet_with_better_audio_links():
    """Update the Google Sheet with improved audio link formats"""
    
    print("🔄 Updating Google Sheet with better audio links...")
    
    try:
        sheets = GoogleSheetsService()
        
        # The file ID from the existing submission
        file_id = '1OBDOsT6gf3fVi-yqVRuIW0mTgL3I0Ekv'
        
        # Create the improved link formats
        preview_link = f"https://drive.google.com/file/d/{file_id}/preview"
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        view_link = f"https://drive.google.com/file/d/{file_id}/view"
        
        print("📝 New Google Sheets Setup:")
        print("=" * 50)
        print("Recommended column structure:")
        print("A: Name")
        print("B: Address") 
        print("C: Phone")
        print("D: Telegram")
        print("E: Audio Preview (Play)")
        print("F: Download")
        print("G: View")
        print("H: Submitted At")
        print("I: Status")
        print("J: Comments")
        
        print("\n🎵 Audio Link Formulas:")
        print("=" * 50)
        print(f"E2: =HYPERLINK(\"{preview_link}\", \"🎵 Play Audio\")")
        print(f"F2: =HYPERLINK(\"{download_link}\", \"📥 Download\")")
        print(f"G2: =HYPERLINK(\"{view_link}\", \"👁️ View\")")
        
        print("\n✅ Instructions:")
        print("=" * 50)
        print("1. Open your Google Sheet")
        print("2. Update the column headers as shown above")
        print("3. Copy the formulas into the respective cells")
        print("4. The '🎵 Play Audio' link will open Google Drive's audio player")
        print("5. This provides the best audio playback experience in Google Sheets")
        
        print(f"\n🔗 Direct Links for Testing:")
        print("=" * 50)
        print(f"Preview (Best): {preview_link}")
        print(f"Download: {download_link}")
        print(f"View: {view_link}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(update_sheet_with_better_audio_links())
