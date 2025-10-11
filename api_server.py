import os
import asyncio
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import jwt
from datetime import datetime, timedelta
from functools import wraps
from database_optimized import DatabaseOptimized
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-key-change-in-production')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Initialize database
db = DatabaseOptimized()

def token_required(f):
    """Decorator to require JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate admin user"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Generate JWT token
        token = jwt.encode(
            {'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
            SECRET_KEY,
            algorithm='HS256'
        )
        
        return jsonify({
            'success': True,
            'token': token,
            'username': username
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/submissions', methods=['GET'])
@token_required
def get_submissions():
    """Get all submissions with optional filtering, pagination, and search"""
    try:
        status = request.args.get('status')
        search_query = request.args.get('search', '').strip()
        limit = int(request.args.get('limit', 100))  # Default to 100 per page
        offset = int(request.args.get('offset', 0))
        page = int(request.args.get('page', 1))
        
        # Calculate offset from page number
        if page > 1:
            offset = (page - 1) * limit
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get submissions and total count with search
        submissions = loop.run_until_complete(
            db.get_all_submissions(status=status, search_query=search_query, limit=limit, offset=offset)
        )
        total_count = loop.run_until_complete(
            db.get_submission_count(status=status, search_query=search_query)
        )
        loop.close()
        
        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'success': True,
            'submissions': submissions,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'search_query': search_query
        })
    except Exception as e:
        logger.error(f"Error fetching submissions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>', methods=['GET'])
@token_required
def get_submission(submission_id):
    """Get a single submission by ID"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        submission = loop.run_until_complete(db.get_submission_by_id(submission_id))
        loop.close()
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        return jsonify({
            'success': True,
            'submission': submission
        })
    except Exception as e:
        logger.error(f"Error fetching submission: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>/status', methods=['PUT'])
@token_required
def update_submission_status(submission_id):
    """Update submission status"""
    try:
        data = request.get_json()
        status = data.get('status')
        comments = data.get('comments', '')
        reviewed_by = request.user.get('username', 'admin')
        
        if status not in ['pending', 'approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            db.update_submission_status(
                submission_id, status, comments, reviewed_by
            )
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating submission status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    """Get submission statistics"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(db.get_submission_stats())
        loop.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/audio/<path:file_path>', methods=['GET'])
@token_required
def serve_audio(file_path):
    """Serve audio files"""
    try:
        audio_dir = Path("audio_files")
        full_path = audio_dir / file_path
        
        if not full_path.exists():
            return jsonify({'error': 'Audio file not found'}), 404
        
        # Detect MIME type based on file extension
        if file_path.lower().endswith('.mp3'):
            mimetype = 'audio/mpeg'
        elif file_path.lower().endswith('.ogg') or file_path.lower().endswith('.oga'):
            mimetype = 'audio/ogg'
        elif file_path.lower().endswith('.wav'):
            mimetype = 'audio/wav'
        else:
            mimetype = 'audio/mpeg'  # Default fallback
        
        return send_file(full_path, mimetype=mimetype)
    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

