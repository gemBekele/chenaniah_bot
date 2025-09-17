#!/usr/bin/env python3
"""
Advanced audio player solution for Google Sheets
This creates multiple ways to access and play audio files
"""

import asyncio
from google_services import GoogleSheetsService

async def create_audio_player_sheet():
    """Create a comprehensive audio player setup in Google Sheets"""
    
    print("🎵 Creating Advanced Audio Player Setup for Google Sheets")
    print("=" * 60)
    
    # The file ID from the existing submission
    file_id = '1OBDOsT6gf3fVi-yqVRuIW0mTgL3I0Ekv'
    
    # Different link formats for different use cases
    links = {
        'preview': f"https://drive.google.com/file/d/{file_id}/preview",
        'view': f"https://drive.google.com/file/d/{file_id}/view", 
        'download': f"https://drive.google.com/uc?export=download&id={file_id}",
        'embed': f"https://drive.google.com/file/d/{file_id}/preview?usp=embed_facebook"
    }
    
    print("🔗 Available Audio Links:")
    print(f"1. Preview (Best for playing): {links['preview']}")
    print(f"2. View (Google Drive): {links['view']}")
    print(f"3. Download (Direct): {links['download']}")
    print(f"4. Embed (For websites): {links['embed']}")
    
    print("\n📋 Recommended Google Sheets Setup:")
    print("=" * 60)
    print("Column Headers (Row 1):")
    print("A: Name | B: Address | C: Phone | D: Telegram | E: Audio Preview | F: Download | G: View | H: Submitted | I: Status | J: Comments")
    
    print("\n🎵 Audio Column Formulas:")
    print("=" * 60)
    print(f"E2 (Audio Preview): =HYPERLINK(\"{links['preview']}\", \"🎵 Play Audio\")")
    print(f"F2 (Download): =HYPERLINK(\"{links['download']}\", \"📥 Download\")")
    print(f"G2 (View): =HYPERLINK(\"{links['view']}\", \"👁️ View in Drive\")")
    
    print("\n💡 Pro Tips for Audio Playback:")
    print("=" * 60)
    print("1. Click '🎵 Play Audio' - Opens Google Drive's built-in audio player")
    print("2. Click '📥 Download' - Downloads the file to play locally")
    print("3. Click '👁️ View' - Opens in Google Drive with full controls")
    print("4. Right-click any link → 'Open in new tab' for better experience")
    
    print("\n🔧 Alternative Solutions:")
    print("=" * 60)
    print("1. Use Google Drive mobile app - better audio controls")
    print("2. Download and play with VLC or other media players")
    print("3. Use browser's built-in audio player (Chrome, Firefox)")
    print("4. Create a simple HTML page with embedded audio players")
    
    return links

async def create_html_audio_player():
    """Create an HTML file with embedded audio players for easy access"""
    
    file_id = '1OBDOsT6gf3fVi-yqVRuIW0mTgL3I0Ekv'
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocalist Audio Submissions</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .submission {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .submission h3 {{
            color: #333;
            margin-top: 0;
        }}
        .audio-player {{
            width: 100%;
            margin: 15px 0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }}
        .info-label {{
            font-weight: bold;
            color: #666;
        }}
        .links {{
            margin: 15px 0;
        }}
        .link-btn {{
            display: inline-block;
            background: #4285f4;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }}
        .link-btn:hover {{
            background: #3367d6;
        }}
    </style>
</head>
<body>
    <h1>🎤 Vocalist Audio Submissions</h1>
    
    <div class="submission">
        <h3>Gemechu Girma</h3>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Phone:</div>
                <div>0930304345</div>
            </div>
            <div class="info-item">
                <div class="info-label">Address:</div>
                <div>Addis Ababa</div>
            </div>
            <div class="info-item">
                <div class="info-label">Telegram:</div>
                <div>@Gem_Bek</div>
            </div>
            <div class="info-item">
                <div class="info-label">Submitted:</div>
                <div>2024-09-17 20:46:00</div>
            </div>
        </div>
        
        <h4>🎵 Audio Submission</h4>
        
        <!-- Embedded Google Drive Audio Player -->
        <iframe 
            src="https://drive.google.com/file/d/{file_id}/preview" 
            width="100%" 
            height="100" 
            frameborder="0" 
            allow="autoplay"
            class="audio-player">
        </iframe>
        
        <div class="links">
            <a href="https://drive.google.com/file/d/{file_id}/preview" target="_blank" class="link-btn">
                🎵 Play in Google Drive
            </a>
            <a href="https://drive.google.com/uc?export=download&id={file_id}" class="link-btn">
                📥 Download Audio
            </a>
            <a href="https://drive.google.com/file/d/{file_id}/view" target="_blank" class="link-btn">
                👁️ View Details
            </a>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds to check for new submissions
        setTimeout(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
    """
    
    with open('audio_submissions.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n🌐 Created HTML audio player: audio_submissions.html")
    print(f"Open this file in your browser for the best audio experience!")
    
    return 'audio_submissions.html'

if __name__ == "__main__":
    async def main():
        # Create the audio player setup
        links = await create_audio_player_sheet()
        
        # Create HTML player
        html_file = await create_html_audio_player()
        
        print(f"\n✅ Setup complete!")
        print(f"📁 HTML file created: {html_file}")
        print(f"🔗 Open the HTML file in your browser for embedded audio players")
    
    asyncio.run(main())
