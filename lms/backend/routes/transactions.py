"""
Transaction management routes for VREC Library Management System
"""
from flask import Blueprint, request, jsonify, send_file
from ..utils.jwt_helper import token_required
from ..utils.db_helper import execute_query
import csv
from io import StringIO
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET'])
@token_required
def get_transactions():
    """
    Get transaction history with filters
    """
    try:
        # Get query parameters
        user_id = request.args.get('user_id')
        book_id = request.args.get('book_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = """
            SELECT t.*, 
                   b.title as book_title,
                   b.barcode as book_barcode,
                   u.name as user_name,
                   u.email as user_email
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if user_id:
            query += " AND t.user_id = %s"
            params.append(user_id)
        
        if book_id:
            query += " AND t.book_id = %s"
            params.append(book_id)
            
        if status:
            query += " AND t.status = %s"
            params.append(status)
            
        if start_date:
            query += " AND DATE(t.issue_date) >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(t.issue_date) <= %s"
            params.append(end_date)
            
        # Add sorting
        query += " ORDER BY t.issue_date DESC"
        
        # Execute query
        transactions = execute_query(query, tuple(params) if params else None)
        
        # Format dates for JSON response
        for transaction in transactions:
            if transaction.get('issue_date'):
                transaction['issue_date'] = transaction['issue_date'].isoformat()
            if transaction.get('return_date'):
                transaction['return_date'] = transaction['return_date'].isoformat()
        
        return jsonify({'transactions': transactions}), 200
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@transactions_bp.route('/export', methods=['GET'])
@token_required
def export_transactions():
    """
    Export transactions as CSV
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        # Get query parameters (same as get_transactions)
        user_id = request.args.get('user_id')
        book_id = request.args.get('book_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = """
            SELECT 
                t.allotment_id,
                b.title as book_title,
                b.barcode as book_barcode,
                u.name as user_name,
                u.email as user_email,
                t.status,
                t.issue_date,
                t.return_date
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        # Add filters (same as get_transactions)
        if user_id:
            query += " AND t.user_id = %s"
            params.append(user_id)
        
        if book_id:
            query += " AND t.book_id = %s"
            params.append(book_id)
            
        if status:
            query += " AND t.status = %s"
            params.append(status)
            
        if start_date:
            query += " AND DATE(t.issue_date) >= %s"
            params.append(start_date)
            
        if end_date:
            query += " AND DATE(t.issue_date) <= %s"
            params.append(end_date)
            
        # Add sorting
        query += " ORDER BY t.issue_date DESC"
        
        # Execute query
        transactions = execute_query(query, tuple(params) if params else None)
        
        # Create CSV file
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'allotment_id',
            'book_title',
            'book_barcode',
            'user_name',
            'user_email',
            'status',
            'issue_date',
            'return_date'
        ])
        
        # Write header
        writer.writeheader()
        
        # Write data
        for transaction in transactions:
            # Format dates
            if transaction.get('issue_date'):
                transaction['issue_date'] = transaction['issue_date'].strftime('%Y-%m-%d %H:%M:%S')
            if transaction.get('return_date'):
                transaction['return_date'] = transaction['return_date'].strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow(transaction)
        
        # Prepare response
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@transactions_bp.route('/overdue', methods=['GET'])
@token_required
def get_overdue_books():
    """
    Get list of overdue books
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        query = """
            SELECT t.*,
                   b.title as book_title,
                   b.barcode as book_barcode,
                   u.name as user_name,
                   u.email as user_email
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN users u ON t.user_id = u.id
            WHERE t.status = 'Issued'
            AND DATEDIFF(CURRENT_DATE, t.issue_date) > 14
            ORDER BY t.issue_date ASC
        """
        
        overdue_books = execute_query(query)
        
        # Format dates for JSON response
        for book in overdue_books:
            if book.get('issue_date'):
                book['issue_date'] = book['issue_date'].isoformat()
            if book.get('return_date'):
                book['return_date'] = book['return_date'].isoformat()
            # Calculate days overdue
            issue_date = datetime.fromisoformat(book['issue_date'])
            days_overdue = (datetime.now() - issue_date).days - 14
            book['days_overdue'] = max(0, days_overdue)
        
        return jsonify({'overdue_books': overdue_books}), 200
        
    except Exception as e:
        logger.error(f"Error fetching overdue books: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@transactions_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user_transactions(user_id):
    """
    Get transaction history for a specific user
    """
    try:
        # Check if user is admin or requesting their own transactions
        if request.user['role'] != 'admin' and request.user['user_id'] != user_id:
            return jsonify({'message': 'Unauthorized'}), 403
            
        query = """
            SELECT t.*,
                   b.title as book_title,
                   b.barcode as book_barcode
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            WHERE t.user_id = %s
            ORDER BY t.issue_date DESC
        """
        
        transactions = execute_query(query, (user_id,))
        
        # Format dates for JSON response
        for transaction in transactions:
            if transaction.get('issue_date'):
                transaction['issue_date'] = transaction['issue_date'].isoformat()
            if transaction.get('return_date'):
                transaction['return_date'] = transaction['return_date'].isoformat()
        
        return jsonify({'transactions': transactions}), 200
        
    except Exception as e:
        logger.error(f"Error fetching user transactions: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@transactions_bp.route('/stats', methods=['GET'])
@token_required
def get_transaction_stats():
    """
    Get transaction statistics
    """
    try:
        # Check if user is admin
        if request.user['role'] != 'admin':
            return jsonify({'message': 'Unauthorized'}), 403
            
        # Get total books issued
        total_issued_query = """
            SELECT COUNT(*) as count
            FROM transactions
            WHERE status = 'Issued'
        """
        total_issued = execute_query(total_issued_query)[0]['count']
        
        # Get total books returned
        total_returned_query = """
            SELECT COUNT(*) as count
            FROM transactions
            WHERE status = 'Returned'
        """
        total_returned = execute_query(total_returned_query)[0]['count']
        
        # Get total overdue books
        total_overdue_query = """
            SELECT COUNT(*) as count
            FROM transactions
            WHERE status = 'Issued'
            AND DATEDIFF(CURRENT_DATE, issue_date) > 14
        """
        total_overdue = execute_query(total_overdue_query)[0]['count']
        
        # Get most active users
        active_users_query = """
            SELECT u.name, u.email, COUNT(*) as transaction_count
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            GROUP BY t.user_id
            ORDER BY transaction_count DESC
            LIMIT 5
        """
        active_users = execute_query(active_users_query)
        
        # Get most borrowed books
        popular_books_query = """
            SELECT b.title, COUNT(*) as borrow_count
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            GROUP BY t.book_id
            ORDER BY borrow_count DESC
            LIMIT 5
        """
        popular_books = execute_query(popular_books_query)
        
        return jsonify({
            'total_issued': total_issued,
            'total_returned': total_returned,
            'total_overdue': total_overdue,
            'active_users': active_users,
            'popular_books': popular_books
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching transaction stats: {e}")
        return jsonify({'message': 'Internal server error'}), 500