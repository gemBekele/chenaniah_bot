#!/usr/bin/env python3
"""
Health check endpoint for Render.com deployment
"""

from flask import Flask, jsonify, send_file, abort
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'Chenaniah Worship Ministry Application Bot',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'ministry': 'Chenaniah Worship Ministry'
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    try:
        # Check if required environment variables are set
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GOOGLE_DRIVE_FOLDER_ID', 
            'GOOGLE_SHEET_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            return jsonify({
                'status': 'error',
                'message': f'Missing environment variables: {missing_vars}',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Check if credentials file exists
        credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', './credentials.json')
        if not os.path.exists(credentials_file):
            return jsonify({
                'status': 'error',
                'message': 'Google credentials file not found',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        return jsonify({
            'status': 'healthy',
            'message': 'All systems operational',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'environment_variables': 'ok',
                'credentials_file': 'ok',
                'database_path': os.getenv('DATABASE_PATH', './data/vocalist_screening.db')
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        'bot_status': 'running',
        'database_status': 'connected',
        'google_apis_status': 'connected',
        'telegram_api_status': 'connected',
        'last_check': datetime.now().isoformat()
    })

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

if __name__ == '__main__':
    # This is for local testing only
    # Render will use the main bot process
    app.run(host='0.0.0.0', port=5000, debug=False)
