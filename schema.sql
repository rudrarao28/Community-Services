-- =====================================================================
-- University Community Services Project (SDG 4 - Quality Education)
-- Production MySQL Database Schema for Library Management System
-- =====================================================================

CREATE DATABASE IF NOT EXISTS library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_db;

-- 1. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    INDEX idx_category_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Users Table (Librarians/Admins and Students/Members)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    student_id VARCHAR(50) UNIQUE NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'member') NOT NULL DEFAULT 'member',
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_student_id (student_id),
    INDEX idx_users_role_status (role, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Books Table (Catalog & Real-time Available Copy Tracking)
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    cover_image VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) 
        REFERENCES categories(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_copies CHECK (available_copies <= total_copies AND available_copies >= 0),
    INDEX idx_books_title (title),
    INDEX idx_books_author (author),
    INDEX idx_books_isbn (isbn),
    INDEX idx_books_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Transactions Table (Issue, Due, Return, and Fines)
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    fine_amount DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    status ENUM('issued', 'returned', 'overdue') NOT NULL DEFAULT 'issued',
    CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_transactions_book FOREIGN KEY (book_id) 
        REFERENCES books(id) ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_transactions_user (user_id),
    INDEX idx_transactions_book (book_id),
    INDEX idx_transactions_status (status),
    INDEX idx_transactions_dates (issue_date, due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Reservations Table (Waiting list when books are out of stock)
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    status ENUM('pending', 'notified', 'fulfilled', 'cancelled') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reservations_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_reservations_book FOREIGN KEY (book_id) 
        REFERENCES books(id) ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_reservations_user (user_id),
    INDEX idx_reservations_book (book_id),
    INDEX idx_reservations_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Activity Logs Table (Administrative audit trail)
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_activity_logs_user (user_id),
    INDEX idx_activity_logs_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
