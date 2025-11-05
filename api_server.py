import os
import asyncio
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import jwt
from datetime import datetime, timedelta
from functools import wraps
from database_optimized import DatabaseOptimized
from notification_service import NotificationService
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes - explicitly allow chenaniah.org and chenaniah.com
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://chenaniah.org", "https://www.chenaniah.org", "https://chenaniah.com", "https://www.chenaniah.com", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False,
        "expose_headers": ["Content-Type", "Authorization"]
    }
}, automatic_options=True, send_wildcard=True)

# Configuration
SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-key-change-in-production')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Initialize database
db = DatabaseOptimized()

# Initialize notification service
notification_service = NotificationService()

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

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Authenticate admin user"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        origin = request.headers.get('Origin', '*')
        # Allow requests from chenaniah.org and chenaniah.com
        allowed_origins = [
            'https://chenaniah.org',
            'https://www.chenaniah.org',
            'https://chenaniah.com',
            'https://www.chenaniah.com'
        ]
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response
    
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
        
        response = jsonify({
            'success': True,
            'token': token,
            'username': username
        })
        # Add CORS headers to response
        origin = request.headers.get('Origin', '*')
        allowed_origins = [
            'https://chenaniah.org',
            'https://www.chenaniah.org',
            'https://chenaniah.com',
            'https://www.chenaniah.com'
        ]
        if origin in allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', origin)
        else:
            response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    response = jsonify({'error': 'Invalid credentials'})
    # Add CORS headers to error response too
    origin = request.headers.get('Origin', '*')
    allowed_origins = [
        'https://chenaniah.org',
        'https://www.chenaniah.org',
        'https://chenaniah.com',
        'https://www.chenaniah.com'
    ]
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 401

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
        
        # Get submission data before updating (to get user_id and name for notification)
        submission = loop.run_until_complete(db.get_submission_by_id(submission_id))
        
        if not submission:
            loop.close()
            return jsonify({'error': 'Submission not found'}), 404
        
        # Update submission status
        loop.run_until_complete(
            db.update_submission_status(
                submission_id, status, comments, reviewed_by
            )
        )
        
        # Send notification to applicant if status changed to approved/rejected
        if submission.get('user_id') and status in ['approved', 'rejected']:
            try:
                loop.run_until_complete(
                    notification_service.notify_applicant_status_update(
                        user_id=submission['user_id'],
                        name=submission.get('name', 'Applicant'),
                        status=status,
                        reviewer_comments=comments if comments else None
                    )
                )
            except Exception as notif_error:
                # Log but don't fail the request if notification fails
                logger.warning(f"Failed to send notification to applicant: {notif_error}")
        
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

@app.route('/api/registration/status', methods=['GET'])
@token_required
def get_registration_status():
    """Get current registration status"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        is_open = loop.run_until_complete(db.get_registration_status())
        loop.close()
        
        return jsonify({
            'success': True,
            'registration_open': is_open
        })
    except Exception as e:
        logger.error(f"Error getting registration status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/registration/status', methods=['PUT'])
@token_required
def set_registration_status():
    """Set registration status"""
    try:
        data = request.get_json()
        is_open = data.get('registration_open', True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(db.set_registration_status(is_open))
        loop.close()
        
        return jsonify({
            'success': True,
            'message': f'Registration {"opened" if is_open else "closed"} successfully',
            'registration_open': is_open
        })
    except Exception as e:
        logger.error(f"Error setting registration status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


# Scheduling Endpoints
@app.route('/api/schedule/stats', methods=['GET'])
@token_required
def get_schedule_stats():
    """Get scheduling statistics"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(db.get_schedule_stats())
        loop.close()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error getting schedule stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/appointments', methods=['GET'])
@token_required
def get_appointments():
    """Get all interview appointments"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        appointments = loop.run_until_complete(db.get_appointments())
        loop.close()
        return jsonify({'success': True, 'appointments': appointments})
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/appointments/<int:appointment_id>', methods=['PUT'])
@token_required
def update_appointment_status(appointment_id):
    """Update appointment status"""
    try:
        data = request.get_json()
        status = data.get('status')
        if not status:
            return jsonify({'error': 'Status is required'}), 400
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(db.update_appointment_status(appointment_id, status))
        loop.close()
        if success:
            return jsonify({'success': True, 'message': 'Appointment status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update appointment status'}), 500
    except Exception as e:
        logger.error(f"Error updating appointment status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/time-slots', methods=['GET', 'OPTIONS'])
def get_time_slots():
    """Get time slots for a specific date or all dates"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    try:
        date = request.args.get('date')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        time_slots = loop.run_until_complete(db.get_time_slots(date))
        loop.close()
        return jsonify({'success': True, 'timeSlots': time_slots})
    except Exception as e:
        logger.error(f"Error getting time slots: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/time-slots', methods=['POST'])
@token_required
def create_time_slot():
    """Create a new time slot"""
    try:
        data = request.get_json()
        time = data.get('time')
        date = data.get('date')
        if not time or not date:
            return jsonify({'error': 'Time and date are required'}), 400
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(db.create_time_slot(time, date))
        loop.close()
        if success:
            return jsonify({'success': True, 'message': 'Time slot created successfully'})
        else:
            return jsonify({'error': 'Failed to create time slot'}), 500
    except Exception as e:
        logger.error(f"Error creating time slot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/time-slots/bulk', methods=['POST'])
@token_required
def create_bulk_time_slots():
    """Create multiple time slots in bulk with custom duration"""
    try:
        data = request.get_json()
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        interval_minutes = data.get('interval_minutes', 30)
        location = data.get('location')
        number_of_slots = data.get('number_of_slots')
        
        if not date or not start_time or not end_time:
            return jsonify({'error': 'date, start_time, and end_time are required'}), 400
        if not location:
            return jsonify({'error': 'location is required'}), 400
        
        try:
            start_obj = datetime.strptime(start_time, '%H:%M')
            end_obj = datetime.strptime(end_time, '%H:%M')
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        if end_obj <= start_obj:
            return jsonify({'error': 'end_time must be after start_time'}), 400
        
        slots_created = 0
        slots_skipped = 0
        current_time = start_obj
        
        # If number_of_slots is specified, calculate the interval needed
        if number_of_slots:
            total_minutes = (end_obj - start_obj).total_seconds() / 60
            calculated_interval = int(total_minutes / number_of_slots)
            if calculated_interval < 1:
                calculated_interval = 1
            interval_minutes = calculated_interval
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        slot_count = 0
        while current_time < end_obj:
            time_str = current_time.strftime('%H:%M')
            success = loop.run_until_complete(db.create_time_slot(time_str, date, location))
            if success:
                slots_created += 1
                slot_count += 1
            else:
                slots_skipped += 1
            current_time += timedelta(minutes=interval_minutes)
            
            # Stop if we've created the requested number of slots
            if number_of_slots and slot_count >= number_of_slots:
                break
                
        loop.close()
        return jsonify({
            'success': True,
            'message': f'Created {slots_created} time slots, skipped {slots_skipped} existing slots',
            'slots_created': slots_created,
            'slots_skipped': slots_skipped
        })
    except Exception as e:
        logger.error(f"Error creating bulk time slots: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/time-slots/<int:slot_id>', methods=['PUT'])
@token_required
def update_time_slot(slot_id):
    """Update time slot availability"""
    try:
        data = request.get_json()
        available = data.get('available')
        if available is None:
            return jsonify({'error': 'Available status is required'}), 400
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(db.update_time_slot_availability(slot_id, available))
        loop.close()
        if success:
            return jsonify({'success': True, 'message': 'Time slot updated successfully'})
        else:
            return jsonify({'error': 'Failed to update time slot'}), 500
    except Exception as e:
        logger.error(f"Error updating time slot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/verify-applicant', methods=['POST', 'OPTIONS'])
def verify_applicant():
    """Verify if a phone number belongs to an applicant by checking last 8 digits"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.get_json()
        phone = data.get('phone', '')
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number is required'}), 400
        
        # Extract last 8 digits from phone number
        import re
        digits_only = re.sub(r'\D', '', phone)
        if len(digits_only) < 8:
            return jsonify({'success': False, 'is_applicant': False, 'error': 'Phone number too short'}), 400
        
        last_8_digits = digits_only[-8:]
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get all submissions and check if any phone number ends with these 8 digits
        submissions = loop.run_until_complete(db.get_all_submissions())
        loop.close()
        
        is_applicant = False
        applicant_name = None
        
        for submission in submissions:
            sub_phone = submission.get('phone', '')
            sub_digits = re.sub(r'\D', '', sub_phone)
            if len(sub_digits) >= 8 and sub_digits[-8:] == last_8_digits:
                is_applicant = True
                applicant_name = submission.get('name', '')
                break
        
        return jsonify({
            'success': True,
            'is_applicant': is_applicant,
            'applicant_name': applicant_name
        })
    except Exception as e:
        logger.error(f"Error verifying applicant: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/schedule/appointments', methods=['POST'])
def create_appointment():
    """Create a new interview appointment"""
    try:
        data = request.get_json()
        required_fields = ['applicant_name', 'applicant_phone', 'scheduled_date', 'scheduled_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        appointment_id = loop.run_until_complete(db.create_appointment(
            data['applicant_name'], 
            data.get('applicant_email', ''), 
            data['applicant_phone'],
            data['scheduled_date'], 
            data['scheduled_time'], 
            data.get('notes', '')
        ))
        
        # Mark the time slot as unavailable (booked)
        if appointment_id:
            slots = loop.run_until_complete(db.get_time_slots(data['scheduled_date']))
            for slot in slots:
                if slot['time'] == data['scheduled_time']:
                    loop.run_until_complete(db.update_time_slot_availability(slot['id'], False))
                    break
        
        loop.close()
        if appointment_id:
            return jsonify({'success': True, 'appointment_id': appointment_id, 'message': 'Appointment created successfully'})
        else:
            return jsonify({'error': 'Failed to create appointment'}), 500
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

