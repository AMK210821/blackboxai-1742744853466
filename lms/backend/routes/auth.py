"""
Authentication routes for VREC Library Management System
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from backend.utils.db_helper import execute_query
from backend.utils.jwt_helper import token_required
from config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if not email or not password or not role:
            return jsonify({'error': 'Missing required fields'}), 400

        # Query user from database
        query = "SELECT * FROM users WHERE email = %s AND role = %s"
        user = execute_query(query, (email, role), fetch_one=True)

        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate JWT token
        token = jwt.encode({
            'user_id': user['user_id'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
        }, JWT_SECRET_KEY)

        return jsonify({
            'token': token,
            'user': {
                'id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        stream = data.get('stream')
        branch = data.get('branch')

        if not all([name, email, password, role, stream, branch]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user already exists
        query = "SELECT * FROM users WHERE email = %s"
        existing_user = execute_query(query, (email,), fetch_one=True)

        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert new user
        query = """
            INSERT INTO users (name, email, password, role, stream_id, course_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (name, email, hashed_password, role, stream, branch))

        return jsonify({'message': 'Registration successful'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        # Query user details including academic information
        query = """
            SELECT u.*, s.name as stream_name, c.name as course_name 
            FROM users u 
            LEFT JOIN streams s ON u.stream_id = s.stream_id 
            LEFT JOIN courses c ON u.course_id = c.course_id 
            WHERE u.user_id = %s
        """
        user = execute_query(query, (current_user['user_id'],), fetch_one=True)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': {
                'id': user['user_id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'stream': user['stream_name'],
                'branch': user['course_name']
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        # Update basic information
        if name or email:
            query = "UPDATE users SET name = %s, email = %s WHERE user_id = %s"
            execute_query(query, (
                name or current_user['name'],
                email or current_user['email'],
                current_user['user_id']
            ))

        # Update password if provided
        if current_password and new_password:
            # Verify current password
            query = "SELECT password FROM users WHERE user_id = %s"
            user = execute_query(query, (current_user['user_id'],), fetch_one=True)

            if not check_password_hash(user['password'], current_password):
                return jsonify({'error': 'Current password is incorrect'}), 401

            # Update password
            hashed_password = generate_password_hash(new_password)
            query = "UPDATE users SET password = %s WHERE user_id = %s"
            execute_query(query, (hashed_password, current_user['user_id']))

        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500