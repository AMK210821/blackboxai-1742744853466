"""
Book management routes for VREC Library Management System
"""
from flask import Blueprint, request, jsonify
from ..utils.jwt_helper import token_required
from ..utils.db_helper import execute_query
from ..config import BOOK_STATUS
import uuid
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
books_bp = Blueprint('books', __name__)

@books_bp.route('/', methods=['GET'])
@token_required
def get_books():
    """
    Get list of books with optional filters
    """
    try:
        # Get query parameters
        subject_id = request.args.get('subject_id')
        status = request.args.get('status')
        search = request.args.get('search')
        
        # Base query
        query = """
            SELECT b.*, s.name as subject_name, c.name as course_name 
            FROM books b
            LEFT JOIN subjects s ON b.subject_id = s.subject_id
            LEFT JOIN courses c ON s.course_id = c.course_id
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if subject_id:
            query += " AND b.subject_id = %s"
            params.append(subject_id)
        
        if status:
            query += " AND b.status = %s"
            params.append(status)
            
        if search:
            query += " AND (b.title LIKE %s OR b.author LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
            
        # Execute query
        books = execute_query(query, tuple(params) if params else None)
        
        return jsonify({'books': books}), 200
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/<book_id>', methods=['GET'])
@token_required
def get_book(book_id):
    """
    Get single book details
    """
    try:
        query = """
            SELECT b.*, s.name as subject_name, c.name as course_name 
            FROM books b
            LEFT JOIN subjects s ON b.subject_id = s.subject_id
            LEFT JOIN courses c ON s.course_id = c.course_id
            WHERE b.book_id = %s
        """
        books = execute_query(query, (book_id,))
        
        if not books:
            return jsonify({'message': 'Book not found'}), 404
            
        return jsonify({'book': books[0]}), 200
        
    except Exception as e:
        logger.error(f"Error fetching book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/', methods=['POST'])
@token_required
def add_book():
    """
    Add a new book
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        required_fields = ['title', 'author', 'subject_id', 'barcode']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Check if barcode already exists
        existing = execute_query(
            "SELECT book_id FROM books WHERE barcode = %s",
            (data['barcode'],)
        )
        
        if existing:
            return jsonify({'message': 'Barcode already exists'}), 409
            
        # Create new book
        book_id = str(uuid.uuid4())
        query = """
            INSERT INTO books (book_id, title, author, subject_id, barcode, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(
            query,
            (
                book_id,
                data['title'],
                data['author'],
                data['subject_id'],
                data['barcode'],
                BOOK_STATUS['AVAILABLE']
            ),
            fetch=False
        )
        
        return jsonify({
            'message': 'Book added successfully',
            'book_id': book_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/<book_id>', methods=['PUT'])
@token_required
def update_book(book_id):
    """
    Update book details
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        data = request.get_json()
        allowed_fields = ['title', 'author', 'subject_id']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({'message': 'No valid fields to update'}), 400
            
        # Build update query
        set_clause = ', '.join(f"{k} = %s" for k in update_data.keys())
        query = f"UPDATE books SET {set_clause} WHERE book_id = %s"
        
        # Execute update
        params = (*update_data.values(), book_id)
        execute_query(query, params, fetch=False)
        
        return jsonify({'message': 'Book updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/allot', methods=['POST'])
@token_required
def allot_book():
    """
    Allot a book to a user
    """
    try:
        data = request.get_json()
        required_fields = ['book_id', 'user_id']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Check if book exists and is available
        books = execute_query(
            "SELECT status FROM books WHERE book_id = %s",
            (data['book_id'],)
        )
        
        if not books:
            return jsonify({'message': 'Book not found'}), 404
            
        if books[0]['status'] != BOOK_STATUS['AVAILABLE']:
            return jsonify({'message': 'Book is not available'}), 400
            
        # Create transaction and update book status
        allotment_id = str(uuid.uuid4())
        
        # Start transaction
        execute_query(
            "UPDATE books SET status = %s WHERE book_id = %s",
            (BOOK_STATUS['ISSUED'], data['book_id']),
            fetch=False
        )
        
        execute_query(
            """
            INSERT INTO transactions 
            (allotment_id, book_id, user_id, status, issue_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                allotment_id,
                data['book_id'],
                data['user_id'],
                'Issued',
                datetime.now()
            ),
            fetch=False
        )
        
        return jsonify({
            'message': 'Book allotted successfully',
            'allotment_id': allotment_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error allotting book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/return', methods=['POST'])
@token_required
def return_book():
    """
    Process book return
    """
    try:
        data = request.get_json()
        if 'book_id' not in data:
            return jsonify({'message': 'Missing book_id'}), 400
            
        # Check if book is issued
        books = execute_query(
            "SELECT status FROM books WHERE book_id = %s",
            (data['book_id'],)
        )
        
        if not books:
            return jsonify({'message': 'Book not found'}), 404
            
        if books[0]['status'] != BOOK_STATUS['ISSUED']:
            return jsonify({'message': 'Book is not issued'}), 400
            
        # Update book status and transaction
        execute_query(
            "UPDATE books SET status = %s WHERE book_id = %s",
            (BOOK_STATUS['AVAILABLE'], data['book_id']),
            fetch=False
        )
        
        execute_query(
            """
            UPDATE transactions 
            SET status = %s, return_date = %s
            WHERE book_id = %s AND status = 'Issued'
            """,
            ('Returned', datetime.now(), data['book_id']),
            fetch=False
        )
        
        return jsonify({'message': 'Book returned successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error returning book: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@books_bp.route('/preorder', methods=['POST'])
@token_required
def preorder_book():
    """
    Handle book preorder
    """
    try:
        data = request.get_json()
        required_fields = ['book_id', 'payment_status']
        
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        # Check if book is available
        books = execute_query(
            "SELECT status FROM books WHERE book_id = %s",
            (data['book_id'],)
        )
        
        if not books:
            return jsonify({'message': 'Book not found'}), 404
            
        if books[0]['status'] != BOOK_STATUS['AVAILABLE']:
            return jsonify({'message': 'Book is not available'}), 400
            
        # Create preorder
        preorder_id = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(hours=8)  # Set to 3:30 PM
        
        execute_query(
            """
            INSERT INTO preorders 
            (preorder_id, book_id, user_id, payment_status, expiry_time)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                preorder_id,
                data['book_id'],
                request.user['user_id'],
                data['payment_status'],
                expiry_time
            ),
            fetch=False
        )
        
        # Update book status
        execute_query(
            "UPDATE books SET status = %s WHERE book_id = %s",
            (BOOK_STATUS['PREORDERED'], data['book_id']),
            fetch=False
        )
        
        return jsonify({
            'message': 'Book preordered successfully',
            'preorder_id': preorder_id,
            'expiry_time': expiry_time.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error preordering book: {e}")
        return jsonify({'message': 'Internal server error'}), 500