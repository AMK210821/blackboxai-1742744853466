"""
Frontend routes for VREC Library Management System
"""
from flask import Blueprint, render_template

# Create blueprint
frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def index():
    return render_template('login.html')

@frontend_bp.route('/login')
def login():
    return render_template('login.html')

@frontend_bp.route('/register')
def register():
    return render_template('register.html')

@frontend_bp.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@frontend_bp.route('/faculty-dashboard')
def faculty_dashboard():
    return render_template('faculty_dashboard.html')

@frontend_bp.route('/student-dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')