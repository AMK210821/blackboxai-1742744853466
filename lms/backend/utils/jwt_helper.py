"""
JWT helper utilities for token generation and validation
"""
import jwt
from datetime import datetime, timezone
from ..config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_token(user_data):
    """
    Generates a JWT token for the given user data
    
    Args:
        user_data (dict): User information to encode in token
        
    Returns:
        str: JWT token
    """
    try:
        payload = {
            'user_id': user_data['id'],
            'role': user_data['role'],
            'exp': datetime.now(timezone.utc) + JWT_ACCESS_TOKEN_EXPIRES
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise

def decode_token(token):
    """
    Decodes and validates a JWT token
    
    Args:
        token (str): JWT token to decode
        
    Returns:
        dict: Decoded token payload
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise

def token_required(f):
    """
    Decorator for protecting routes with JWT
    """
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Decode token
            payload = decode_token(token)
            request.user = payload
        except Exception as e:
            return jsonify({'message': str(e)}), 401
            
        return f(*args, **kwargs)
    
    return decorated