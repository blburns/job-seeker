"""
Configuration Validation System
Validates application configuration and provides helpful error messages
"""

import os
from typing import Dict, List, Tuple, Any
from flask import Flask


class ConfigurationValidator:
    """Validates application configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_configuration(self, app: Flask) -> Tuple[bool, List[str], List[str]]:
        """
        Validate application configuration
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate required settings
        self._validate_required_settings(app)
        
        # Validate database configuration
        self._validate_database_config(app)
        
        # Validate security settings
        self._validate_security_config(app)
        
        # Validate email configuration
        self._validate_email_config(app)
        
        # Validate environment-specific settings
        self._validate_environment_config(app)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_required_settings(self, app: Flask) -> None:
        """Validate required application settings"""
        required_settings = [
            'SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI',
            'JWT_SECRET_KEY'
        ]
        
        for setting in required_settings:
            if not app.config.get(setting):
                self.errors.append(f"Required setting '{setting}' is not configured")
    
    def _validate_database_config(self, app: Flask) -> None:
        """Validate database configuration"""
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            return
        
        # Check for default/unsafe values
        if 'dev-secret-key' in str(app.config.get('SECRET_KEY', '')):
            self.warnings.append("Using default SECRET_KEY - change in production")
        
        if 'jwt-secret-key' in str(app.config.get('JWT_SECRET_KEY', '')):
            self.warnings.append("Using default JWT_SECRET_KEY - change in production")
        
        # Validate database URI format
        if db_uri.startswith('sqlite:///'):
            # SQLite configuration
            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.exists(os.path.dirname(db_path)):
                self.warnings.append(f"SQLite database directory does not exist: {os.path.dirname(db_path)}")
        elif db_uri.startswith('postgresql://'):
            # PostgreSQL configuration
            if not app.config.get('DB_HOST'):
                self.warnings.append("PostgreSQL host not specified - using default")
        elif db_uri.startswith('mysql'):
            # MySQL configuration
            if not app.config.get('DB_HOST'):
                self.warnings.append("MySQL host not specified - using default")
    
    def _validate_security_config(self, app: Flask) -> None:
        """Validate security configuration"""
        # Check CSRF protection
        if not app.config.get('WTF_CSRF_ENABLED', True):
            self.warnings.append("CSRF protection is disabled")
        
        # Check session security
        if app.config.get('FLASK_ENV') == 'production':
            if not app.config.get('SESSION_COOKIE_SECURE', False):
                self.warnings.append("Session cookies not secure in production")
            
            if not app.config.get('SESSION_COOKIE_HTTPONLY', False):
                self.warnings.append("Session cookies not HTTP-only in production")
        
        # Check password requirements
        max_content_length = app.config.get('MAX_CONTENT_LENGTH', 0)
        if max_content_length > 50 * 1024 * 1024:  # 50MB
            self.warnings.append("Maximum content length is very large - consider security implications")
    
    def _validate_email_config(self, app: Flask) -> None:
        """Validate email configuration"""
        mail_server = app.config.get('MAIL_SERVER')
        if not mail_server:
            self.warnings.append("Email server not configured - email features will not work")
            return
        
        # Check for required email settings
        required_email_settings = ['MAIL_USERNAME', 'MAIL_PASSWORD']
        for setting in required_email_settings:
            if not app.config.get(setting):
                self.warnings.append(f"Email setting '{setting}' not configured")
    
    def _validate_environment_config(self, app: Flask) -> None:
        """Validate environment-specific configuration"""
        flask_env = app.config.get('FLASK_ENV', 'development')
        
        if flask_env == 'production':
            # Production-specific validations
            if app.config.get('FLASK_DEBUG', False):
                self.errors.append("Debug mode should be disabled in production")
            
            if not app.config.get('SECRET_KEY') or len(app.config.get('SECRET_KEY', '')) < 32:
                self.errors.append("SECRET_KEY should be at least 32 characters in production")
        
        elif flask_env == 'development':
            # Development-specific validations
            if not app.config.get('FLASK_DEBUG', False):
                self.warnings.append("Debug mode is disabled in development")
    
    def get_configuration_summary(self, app: Flask) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'environment': app.config.get('FLASK_ENV', 'development'),
            'debug_mode': app.config.get('FLASK_DEBUG', False),
            'database_type': app.config.get('DATABASE_TYPE', 'unknown'),
            'csrf_enabled': app.config.get('WTF_CSRF_ENABLED', True),
            'email_configured': bool(app.config.get('MAIL_SERVER')),
            'cache_type': app.config.get('CACHE_TYPE', 'simple'),
            'max_content_length': app.config.get('MAX_CONTENT_LENGTH', 0),
            'log_level': app.config.get('LOG_LEVEL', 'INFO')
        }


def validate_configuration(app: Flask) -> Tuple[bool, List[str], List[str]]:
    """
    Validate application configuration
    
    Args:
        app: Flask application instance
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ConfigurationValidator()
    return validator.validate_configuration(app)


def init_configuration_validation(app: Flask) -> None:
    """Initialize configuration validation"""
    is_valid, errors, warnings = validate_configuration(app)
    
    # Log warnings
    for warning in warnings:
        app.logger.warning(f"Configuration warning: {warning}")
    
    # Log errors and raise exception if critical
    for error in errors:
        app.logger.error(f"Configuration error: {error}")
    
    if not is_valid:
        raise RuntimeError(f"Configuration validation failed: {', '.join(errors)}")
    
    # Log configuration summary
    validator = ConfigurationValidator()
    summary = validator.get_configuration_summary(app)
    app.logger.info(f"Configuration validated successfully: {summary}")
