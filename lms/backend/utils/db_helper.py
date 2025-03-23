"""
Database helper utilities for SQLite connections and operations
"""
import sqlite3
from sqlite3 import Error
from ..config import DATABASE_PATH
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """
    Creates and returns a connection to the SQLite database
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = dict_factory
        return connection
    except Error as e:
        logger.error(f"Error connecting to SQLite database: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """
    Executes a SQL query and returns the result
    
    Args:
        query (str): SQL query to execute
        params (tuple): Parameters for the query
        fetch (bool): Whether to fetch and return results
    
    Returns:
        list: Query results if fetch is True, else None
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch:
            return cursor.fetchall()
        else:
            connection.commit()
            return cursor.lastrowid
            
    except Error as e:
        logger.error(f"Error executing query: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def execute_many(query, params_list):
    """
    Executes multiple SQL queries in a transaction
    
    Args:
        query (str): SQL query to execute
        params_list (list): List of parameter tuples
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.executemany(query, params_list)
        connection.commit()
        
    except Error as e:
        logger.error(f"Error executing multiple queries: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def init_db():
    """Initialize the database with schema"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT CHECK(role IN ('admin', 'faculty', 'student')) NOT NULL,
                stream TEXT,
                branch TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create streams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                stream_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                stream_id TEXT,
                semesters INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
            )
        ''')

        # Create subjects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                course_id TEXT,
                semester INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )
        ''')

        # Create books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                subject_id TEXT,
                title TEXT NOT NULL,
                author TEXT,
                barcode TEXT UNIQUE NOT NULL,
                status TEXT CHECK(status IN ('Available', 'Issued', 'Preordered')) DEFAULT 'Available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE SET NULL
            )
        ''')

        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                allotment_id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT CHECK(status IN ('Issued', 'Returned', 'Overdue')) NOT NULL,
                issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                return_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Create preorders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preorders (
                preorder_id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                payment_status TEXT CHECK(payment_status IN ('Pending', 'Completed')) DEFAULT 'Pending',
                expiry_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Insert default admin account if it doesn't exist
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, name, role, email, password)
            VALUES (
                'admin-001',
                'VREC Admin',
                'admin',
                'vrec_admin',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfJAAcxkGqJ7ZAe'
            )
        ''')

        # Insert sample streams if they don't exist
        cursor.executemany('''
            INSERT OR IGNORE INTO streams (stream_id, name)
            VALUES (?, ?)
        ''', [
            ('stream-001', 'Engineering'),
            ('stream-002', 'Management'),
            ('stream-003', 'Sciences')
        ])

        # Insert sample courses if they don't exist
        cursor.executemany('''
            INSERT OR IGNORE INTO courses (course_id, name, stream_id, semesters)
            VALUES (?, ?, ?, ?)
        ''', [
            ('course-001', 'Computer Science Engineering', 'stream-001', 8),
            ('course-002', 'Electronics Engineering', 'stream-001', 8),
            ('course-003', 'Mechanical Engineering', 'stream-001', 8)
        ])

        connection.commit()
        logger.info("Database initialized successfully")

    except Error as e:
        logger.error(f"Error initializing database: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()