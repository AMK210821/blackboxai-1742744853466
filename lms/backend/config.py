"""
Configuration settings for the VREC Library Management System
"""
import os
from datetime import timedelta

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vrec_lms.db')

# JWT Configuration
JWT_SECRET_KEY = 'your-secret-key-here'  # Change in production
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

# Application Configuration
DEBUG = True
HOST = '0.0.0.0'  # Allow external connections
PORT = 8000       # Use port 8000 for web environment

# Book Status
BOOK_STATUS = {
    'AVAILABLE': 'Available',
    'ISSUED': 'Issued',
    'PREORDERED': 'Preordered'
}

# Transaction Status
TRANSACTION_STATUS = {
    'ISSUED': 'Issued',
    'RETURNED': 'Returned',
    'OVERDUE': 'Overdue'
}

# Preorder Configuration
PREORDER_AMOUNT = 10  # Amount in INR
PREORDER_EXPIRY_TIME = '15:30'  # 24-hour format

# File paths
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}