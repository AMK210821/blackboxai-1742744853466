"""
Main Flask application for VREC Library Management System
"""
from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import DEBUG, HOST, PORT
from backend.utils.db_helper import init_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../static',
            template_folder='../templates')

# Enable CORS
CORS(app)

# Load configuration
app.config.from_object('backend.config')

# Import routes
from backend.routes.frontend import frontend_bp
from backend.routes.auth import auth_bp
from backend.routes.books import books_bp
from backend.routes.transactions import transactions_bp
from backend.routes.academic import academic_bp

# Register blueprints
app.register_blueprint(frontend_bp)  # Register frontend routes
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(books_bp, url_prefix='/api/books')
app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
app.register_blueprint(academic_bp, url_prefix='/api/academic')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    try:
        # Initialize the database
        init_db()
        
        # Create upload folder if it doesn't exist
        from backend.config import UPLOAD_FOLDER
        import os
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        # Run the application
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")