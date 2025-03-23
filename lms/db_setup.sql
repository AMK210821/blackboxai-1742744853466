-- MySQL Database Setup for VREC College LMS

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS vrec_lms;
USE vrec_lms;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'faculty', 'student') NOT NULL,
    stream VARCHAR(50),
    branch VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Streams table
CREATE TABLE IF NOT EXISTS streams (
    stream_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stream_id VARCHAR(36),
    semesters INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
);

-- Subjects table
CREATE TABLE IF NOT EXISTS subjects (
    subject_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    course_id VARCHAR(36),
    semester INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

-- Books table
CREATE TABLE IF NOT EXISTS books (
    book_id VARCHAR(36) PRIMARY KEY,
    subject_id VARCHAR(36),
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100),
    barcode VARCHAR(50) UNIQUE NOT NULL,
    status ENUM('Available', 'Issued', 'Preordered') DEFAULT 'Available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE SET NULL
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    allotment_id VARCHAR(36) PRIMARY KEY,
    book_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    status ENUM('Issued', 'Returned', 'Overdue') NOT NULL,
    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Preorders table
CREATE TABLE IF NOT EXISTS preorders (
    preorder_id VARCHAR(36) PRIMARY KEY,
    book_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    payment_status ENUM('Pending', 'Completed') DEFAULT 'Pending',
    expiry_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_books_barcode ON books(barcode);

-- Insert default admin account
-- Password: admin123 (hashed version will be updated in the application)
INSERT INTO users (id, name, role, email, password) 
VALUES (
    'admin-001',
    'VREC Admin',
    'admin',
    'vrecl_admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfJAAcxkGqJ7ZAe'
) ON DUPLICATE KEY UPDATE id=id;

-- Insert sample streams
INSERT INTO streams (stream_id, name) VALUES
('stream-001', 'Engineering'),
('stream-002', 'Management'),
('stream-003', 'Sciences')
ON DUPLICATE KEY UPDATE stream_id=stream_id;

-- Insert sample courses for Engineering stream
INSERT INTO courses (course_id, name, stream_id, semesters) VALUES
('course-001', 'Computer Science Engineering', 'stream-001', 8),
('course-002', 'Electronics Engineering', 'stream-001', 8),
('course-003', 'Mechanical Engineering', 'stream-001', 8)
ON DUPLICATE KEY UPDATE course_id=course_id;