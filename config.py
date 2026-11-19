import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'sdg4-edu-lms-super-secret-key-change-in-prod')
    
    # Database Configuration:
    # Priority:
    # 1. DATABASE_URL from .env (e.g. mysql+pymysql://root:password@localhost:3306/library_db)
    # 2. SQLite local fallback for zero-setup execution if MySQL is not configured locally
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(basedir, 'library.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session & Security Settings
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Library Domain Business Logic Rules
    MAX_BORROW_LIMIT = int(os.getenv('MAX_BORROW_LIMIT', '3'))
    BORROW_DURATION_DAYS = int(os.getenv('BORROW_DURATION_DAYS', '14'))
    FINE_PER_DAY = float(os.getenv('FINE_PER_DAY', '2.0'))  # Rs. 2.00 per late day
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max cover image
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}


class TestingConfig(Config):
    """Configuration for automated test suite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
