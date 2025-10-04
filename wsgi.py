#!/usr/bin/env python3
"""
WSGI entry point for the Chenaniah API server
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ.setdefault('FLASK_APP', 'api_server.py')
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask app
from api_server import app

# WSGI application
application = app

if __name__ == "__main__":
    # For development/testing
    port = int(os.getenv('API_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
