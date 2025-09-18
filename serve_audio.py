#!/usr/bin/env python3
"""
Simple HTTP server to serve audio files
"""

from flask import Flask, send_file, abort
import os
from pathlib import Path

app = Flask(__name__)

@app.route('/audio_files/<path:filename>')
def serve_audio(filename):
    """Serve audio files from local storage"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            abort(403)
        
        # Construct file path
        file_path = Path("audio_files") / filename
        
        # Check if file exists
        if not file_path.exists():
            abort(404)
        
        # Serve the file
        return send_file(
            file_path,
            as_attachment=False,
            mimetype='audio/mpeg'
        )
    
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        abort(500)

if __name__ == "__main__":
    # Create audio_files directory if it doesn't exist
    Path("audio_files").mkdir(exist_ok=True)
    
    # Run the server
    app.run(host='0.0.0.0', port=5001, debug=False)
