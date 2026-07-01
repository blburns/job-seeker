"""
Core Extensions Package
Central place to initialize Flask extensions (SQLAlchemy, Bcrypt, etc.)
Improved version of dreamlikelabs-site extensions
"""

# Import core extensions
from .core import (
    db, 
    bcrypt, 
    login_manager, 
    csrf, 
    limiter,
    cache,
    jwt
)

# Import configuration functions
from .config import (
    init_config,
    load_environment_variables
)

# Import blueprint registration
from .blueprints import register_blueprints

# Import extension initialization
from .initialization import (
    init_extensions,
    init_migrations,
    init_login_manager
)

# Import template context
from .template_context import init_template_context

# Import health monitoring
from .monitoring import init_health_monitoring, stop_health_monitoring, health_checker

# Import logging configuration
from .logging_config import init_logging_config

# Import CSRF configuration
from .csrf_config import init_csrf_config

# Import secret management
from .secret_management import init_secret_management

# Import configuration validation
from .configuration_validation import init_configuration_validation

# Import configuration testing
from .configuration_testing import init_configuration_testing

# Import database health monitoring
from .database_health import init_database_health_monitoring

# Import database backup
from .database_backup import init_database_backup

# Import migration testing
from .migration_testing import init_migration_testing

# Import cache system
from .cache import init_cache

# Import email service
from .email_init import init_email_service

# Import OAuth service
from .oauth_init import init_oauth_service

__all__ = [
    # Core extensions
    'db',
    'bcrypt',
    'login_manager',
    'csrf',
    'limiter',
    'cache',
    'jwt',
    
    # Configuration functions
    'init_config',
    'load_environment_variables',
    
    # Blueprint registration
    'register_blueprints',
    
    # Extension initialization
    'init_extensions',
    'init_migrations',
    'init_login_manager',
    
    # Template context
    'init_template_context',
    
    # Health monitoring
    'init_health_monitoring',
    'stop_health_monitoring',
    'health_checker',
    
    # Logging and security
    'init_logging_config',
    'init_csrf_config',
    
    # Email service
    'init_email_service',
    
    # OAuth service
    'init_oauth_service',
    
    # Secret management and configuration
    'init_secret_management',
    'init_configuration_validation',
    'init_configuration_testing',
    
    # Database management
    'init_database_health_monitoring',
    'init_database_backup',
    'init_migration_testing',
    
    # Cache system
    'init_cache'
]
