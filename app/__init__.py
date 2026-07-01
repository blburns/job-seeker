"""
Core Flask Application Factory
Modern, scalable Flask application boilerplate based on dreamlikelabs-site architecture
"""

import logging
import os
import sys
from typing import Optional
from pathlib import Path
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Add project root to path for version import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from version import get_version, get_phase_info, VERSION_INFO

# Load environment variables
from app.extensions.config import load_environment_variables
load_environment_variables()

from app.extensions import (
    init_extensions,
    init_config,
    init_logging_config,
    init_csrf_config,
    init_template_context,
    register_blueprints,
    init_migrations,
    init_health_monitoring,
    init_login_manager,
    init_secret_management,
    init_configuration_validation,
    init_configuration_testing,
    init_database_health_monitoring,
    init_database_backup,
    init_migration_testing,
    init_cache,
    init_email_service,
    init_oauth_service
)
from app.extensions.error_handlers import register_error_handlers


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory function
    
    Args:
        config_name: Configuration name (development, production, testing)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Only use ProxyFix in production mode (when behind a reverse proxy)
    if os.environ.get('FLASK_ENV') == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    app.url_map.strict_slashes = False

    with app.app_context():
        # Initialize configuration
        init_config(app, config_name)
        
        # Optional: Sentry error tracking (when SENTRY_DSN is set)
        if app.config.get('SENTRY_DSN'):
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                sentry_sdk.init(
                    dsn=app.config['SENTRY_DSN'],
                    environment=app.config.get('SENTRY_ENVIRONMENT', 'development'),
                    integrations=[FlaskIntegration()],
                    traces_sample_rate=0.1,
                )
            except Exception:  # noqa: S110
                pass  # Don't break app if Sentry init fails
        
        # Initialize secret management
        init_secret_management(app)
        
        # Initialize configuration validation
        init_configuration_validation(app)
        
        # Initialize logging
        init_logging_config(app)
        
        # Initialize CSRF protection
        init_csrf_config(app)
        
        # Initialize extensions (database, cache, etc.)
        init_extensions(app)
        
        # Initialize database migrations
        init_migrations(app)
        
        # Initialize database health monitoring
        init_database_health_monitoring(app)
        
        # Initialize database backup system
        init_database_backup(app)
        
        # Initialize migration testing
        init_migration_testing(app)
        
        # Initialize cache system
        init_cache(app)
        
        # Initialize email service
        init_email_service(app)
        
        # Initialize OAuth service
        init_oauth_service(app)
        
        # Initialize login manager (after database is set up)
        init_login_manager(app)
        
        # Initialize template context processors
        init_template_context(app)
        
        # Initialize API
        from app.api import init_api
        init_api(app)
        
        # Register blueprints
        register_blueprints(app)
        
        # Register error handlers
        register_error_handlers(app)
        
        # Initialize health monitoring
        init_health_monitoring(app)
        
        # Initialize configuration testing (development only)
        if config_name == 'development':
            init_configuration_testing(app)

    return app


def create_app_for_cli() -> Flask:
    """Create app instance for CLI commands"""
    return create_app()


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True',
        host=os.getenv('FLASK_RUN_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_RUN_PORT', 5000))
    )
