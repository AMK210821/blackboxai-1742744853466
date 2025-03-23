"""
Academic management routes for VREC Library Management System
"""
from flask import Blueprint, request, jsonify
from ..utils.jwt_helper import token_required
from ..utils.db_helper import execute_query
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
academic_bp = Blueprint('academic', __name__)

@academic_bp.route('/streams', methods=['GET'])
@token_required
def get_streams():
    """
    Get all academic streams
    """
    try:
        query = "SELECT * FROM streams ORDER BY name"
        streams = execute_query(query)
        return jsonify({'streams': streams}), 200
        
    except Exception as e:
        logger.error(f"Error fetching streams: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/streams', methods=['POST'])
@token_required
def add_stream():
    """
    Add a new academic stream
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        if 'name' not in data:
            return jsonify({'message': 'Stream name is required'}), 400
            
        # Check if stream already exists
        existing = execute_query(
            "SELECT stream_id FROM streams WHERE name = %s",
            (data['name'],)
        )
        
        if existing:
            return jsonify({'message': 'Stream already exists'}), 409
            
        # Create new stream
        stream_id = str(uuid.uuid4())
        query = "INSERT INTO streams (stream_id, name) VALUES (%s, %s)"
        execute_query(query, (stream_id, data['name']), fetch=False)
        
        return jsonify({
            'message': 'Stream added successfully',
            'stream_id': stream_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding stream: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/courses', methods=['GET'])
@token_required
def get_courses():
    """
    Get courses with optional stream filter
    """
    try:
        stream_id = request.args.get('stream_id')
        
        query = """
            SELECT c.*, s.name as stream_name
            FROM courses c
            JOIN streams s ON c.stream_id = s.stream_id
        """
        params = None
        
        if stream_id:
            query += " WHERE c.stream_id = %s"
            params = (stream_id,)
            
        query += " ORDER BY s.name, c.name"
        
        courses = execute_query(query, params)
        return jsonify({'courses': courses}), 200
        
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/courses', methods=['POST'])
@token_required
def add_course():
    """
    Add a new course
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        required_fields = ['name', 'stream_id', 'semesters']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Check if course already exists in stream
        existing = execute_query(
            "SELECT course_id FROM courses WHERE name = %s AND stream_id = %s",
            (data['name'], data['stream_id'])
        )
        
        if existing:
            return jsonify({'message': 'Course already exists in this stream'}), 409
            
        # Create new course
        course_id = str(uuid.uuid4())
        query = """
            INSERT INTO courses (course_id, name, stream_id, semesters)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(
            query,
            (course_id, data['name'], data['stream_id'], data['semesters']),
            fetch=False
        )
        
        return jsonify({
            'message': 'Course added successfully',
            'course_id': course_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding course: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/subjects', methods=['GET'])
@token_required
def get_subjects():
    """
    Get subjects with optional course and semester filters
    """
    try:
        course_id = request.args.get('course_id')
        semester = request.args.get('semester')
        
        query = """
            SELECT s.*, c.name as course_name, st.name as stream_name
            FROM subjects s
            JOIN courses c ON s.course_id = c.course_id
            JOIN streams st ON c.stream_id = st.stream_id
            WHERE 1=1
        """
        params = []
        
        if course_id:
            query += " AND s.course_id = %s"
            params.append(course_id)
            
        if semester:
            query += " AND s.semester = %s"
            params.append(semester)
            
        query += " ORDER BY st.name, c.name, s.semester, s.name"
        
        subjects = execute_query(query, tuple(params) if params else None)
        return jsonify({'subjects': subjects}), 200
        
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/subjects', methods=['POST'])
@token_required
def add_subject():
    """
    Add a new subject
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        required_fields = ['name', 'course_id', 'semester']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Validate semester number against course
        course = execute_query(
            "SELECT semesters FROM courses WHERE course_id = %s",
            (data['course_id'],)
        )
        
        if not course:
            return jsonify({'message': 'Course not found'}), 404
            
        if int(data['semester']) > course[0]['semesters']:
            return jsonify({'message': 'Invalid semester number for this course'}), 400
            
        # Check if subject already exists in course and semester
        existing = execute_query(
            """
            SELECT subject_id 
            FROM subjects 
            WHERE name = %s AND course_id = %s AND semester = %s
            """,
            (data['name'], data['course_id'], data['semester'])
        )
        
        if existing:
            return jsonify({
                'message': 'Subject already exists in this course and semester'
            }), 409
            
        # Create new subject
        subject_id = str(uuid.uuid4())
        query = """
            INSERT INTO subjects (subject_id, name, course_id, semester)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(
            query,
            (subject_id, data['name'], data['course_id'], data['semester']),
            fetch=False
        )
        
        return jsonify({
            'message': 'Subject added successfully',
            'subject_id': subject_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding subject: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/hierarchy', methods=['GET'])
@token_required
def get_academic_hierarchy():
    """
    Get complete academic hierarchy (streams -> courses -> subjects)
    """
    try:
        # Get all streams
        streams_query = "SELECT * FROM streams ORDER BY name"
        streams = execute_query(streams_query)
        
        # Get courses for each stream
        for stream in streams:
            courses_query = """
                SELECT * FROM courses 
                WHERE stream_id = %s 
                ORDER BY name
            """
            courses = execute_query(courses_query, (stream['stream_id'],))
            
            # Get subjects for each course
            for course in courses:
                subjects_query = """
                    SELECT * FROM subjects 
                    WHERE course_id = %s 
                    ORDER BY semester, name
                """
                subjects = execute_query(subjects_query, (course['course_id'],))
                
                # Group subjects by semester
                subjects_by_semester = {}
                for subject in subjects:
                    semester = subject['semester']
                    if semester not in subjects_by_semester:
                        subjects_by_semester[semester] = []
                    subjects_by_semester[semester].append(subject)
                
                course['subjects_by_semester'] = subjects_by_semester
            
            stream['courses'] = courses
        
        return jsonify({'academic_hierarchy': streams}), 200
        
    except Exception as e:
        logger.error(f"Error fetching academic hierarchy: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@academic_bp.route('/subjects/<subject_id>/books', methods=['GET'])
@token_required
def get_subject_books(subject_id):
    """
    Get all books for a specific subject
    """
    try:
        query = """
            SELECT b.*, s.name as subject_name, c.name as course_name
            FROM books b
            JOIN subjects s ON b.subject_id = s.subject_id
            JOIN courses c ON s.course_id = c.course_id
            WHERE b.subject_id = %s
            ORDER BY b.title
        """
        
        books = execute_query(query, (subject_id,))
        return jsonify({'books': books}), 200
        
    except Exception as e:
        logger.error(f"Error fetching subject books: {e}")
        return jsonify({'message': 'Internal server error'}), 500