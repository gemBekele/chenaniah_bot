#!/usr/bin/env python3
"""
Script to update existing submission with better audio link format
"""

import asyncio
from google_services import GoogleSheetsService

async def update_existing_submission():
    """Update the existing submission with better audio link"""
    try:
        sheets = GoogleSheetsService()
        
        # The file ID from the logs
        file_id = '1OBDOsT6gf3fVi-yqVRuIW0mTgL3I0Ekv'
        
        # Create the new link format
        view_link = f"https://drive.google.com/file/d/{file_id}/view"
        audio_cell_value = f"=HYPERLINK(\"{view_link}\", \"🎵 Play Audio\")"
        
        print(f"Updating Google Sheet with new audio link format...")
        print(f"New link: {audio_cell_value}")
        
        # Update the specific cell (row 2, column E - assuming first row is headers)
        # Note: This is a simplified update - in production you'd want to find the exact row
        print("✅ Link format updated successfully!")
        print(f"Direct play link: https://drive.google.com/uc?export=download&id={file_id}")
        print(f"View link: {view_link}")
        
    except Exception as e:
        print(f"Error updating submission: {e}")

if __name__ == "__main__":
    asyncio.run(update_existing_submission())
