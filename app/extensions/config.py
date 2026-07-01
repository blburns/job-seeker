"""
Configuration Management
Handles application configuration and environment variables
Enhanced with multi-database support
"""

import os
from typing import Optional
from flask import Flask
from dotenv import load_dotenv
from .database_config import DatabaseConfig


def load_environment_variables() -> None:
    """Load environment variables from multiple sources"""
    # Load from .env file in project root
    load_dotenv()
    
    # Load from .env.local if it exists (for local overrides)
    if os.path.exists('.env.local'):
        load_dotenv('.env.local', override=True)
    
    # Load from system environment variables
    # These will override .env file values


def init_config(app: Flask, config_name: Optional[str] = None) -> None:
    """
    Initialize application configuration with multi-database support
    
    Args:
        app: Flask application instance
        config_name: Configuration name (development, production, testing)
    """
    # Get database configuration
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    db_uri = DatabaseConfig.get_database_uri()
    db_engine_options = DatabaseConfig.get_engine_options(db_type)
    
    # Set default configuration
    app.config.update({
        # Flask Configuration
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'development'),
        'FLASK_DEBUG': os.environ.get('FLASK_DEBUG', 'True') == 'True',
        
        # Database Configuration - Enhanced with multi-database support
        'SQLALCHEMY_DATABASE_URI': db_uri,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': db_engine_options,
        
        # Database Type Information
        'DATABASE_TYPE': db_type,
        'DATABASE_INFO': DatabaseConfig.get_database_info(),
        
        # JWT Configuration
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production'),
        'JWT_ACCESS_TOKEN_EXPIRES': 3600,  # 1 hour
        'JWT_REFRESH_TOKEN_EXPIRES': 2592000,  # 30 days
        
        # Cache Configuration
        'CACHE_TYPE': 'redis' if os.environ.get('REDIS_URL') else 'simple',
        'CACHE_REDIS_URL': os.environ.get('REDIS_URL'),
        'CACHE_DEFAULT_TIMEOUT': 300,
        
        # Rate Limiting
        'RATELIMIT_STORAGE_URL': os.environ.get('REDIS_URL'),
        
        # Email Configuration
        'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'True') == 'True',
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER'),
        
        # Email Service Configuration
        'EMAIL_PROVIDER': os.environ.get('EMAIL_PROVIDER', 'console'),  # console, sendgrid, mailgun, smtp
        'EMAIL_FROM': os.environ.get('EMAIL_FROM', 'noreply@example.com'),
        'EMAIL_FROM_NAME': os.environ.get('EMAIL_FROM_NAME', 'Application'),
        'SENDGRID_API_KEY': os.environ.get('SENDGRID_API_KEY'),
        'MAILGUN_API_KEY': os.environ.get('MAILGUN_API_KEY'),
        'MAILGUN_DOMAIN': os.environ.get('MAILGUN_DOMAIN'),
        'SMTP_HOST': os.environ.get('SMTP_HOST', 'localhost'),
        'SMTP_PORT': int(os.environ.get('SMTP_PORT', 587)),
        'SMTP_USERNAME': os.environ.get('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD'),
        'SMTP_USE_TLS': os.environ.get('SMTP_USE_TLS', 'True') == 'True',
        
        # Application Configuration
        'APP_NAME': os.environ.get('APP_NAME', 'Core Application'),
        'APP_VERSION': os.environ.get('APP_VERSION', '1.0.0'),
        'COMPANY_NAME': os.environ.get('COMPANY_NAME', 'Your Company'),
        
        # OAuth Configuration
        'GOOGLE_CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'MICROSOFT_CLIENT_ID': os.environ.get('MICROSOFT_CLIENT_ID'),
        'MICROSOFT_CLIENT_SECRET': os.environ.get('MICROSOFT_CLIENT_SECRET'),
        'GITHUB_CLIENT_ID': os.environ.get('GITHUB_CLIENT_ID'),
        'GITHUB_CLIENT_SECRET': os.environ.get('GITHUB_CLIENT_SECRET'),
        
        # Security Configuration
        'WTF_CSRF_TIME_LIMIT': 3600,
        'WTF_CSRF_ENABLED': True,
        
        # File Upload Configuration
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        'UPLOAD_FOLDER': os.environ.get('UPLOAD_FOLDER', 'uploads'),
        
        # Logging Configuration
        'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO'),
        'LOG_FILE': os.environ.get('LOG_FILE', 'logs/app.log'),
        # Error tracking (optional: set SENTRY_DSN to enable)
        'SENTRY_DSN': os.environ.get('SENTRY_DSN'),
        'SENTRY_ENVIRONMENT': os.environ.get('SENTRY_ENVIRONMENT', os.environ.get('FLASK_ENV', 'development')),
    })
    
    # Environment-specific configuration
    if config_name == 'production':
        app.config.update({
            'FLASK_DEBUG': False,
            'WTF_CSRF_ENABLED': True,
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
        })
    elif config_name == 'testing':
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'MAIL_SUPPRESS_SEND': True,
        })
    
    # Ensure upload folder exists
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Ensure logs directory exists
    log_file = app.config['LOG_FILE']
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log database configuration
    db_info = app.config['DATABASE_INFO']
    print(f"Database configured: {db_info['name']} ({db_info['type']})")
