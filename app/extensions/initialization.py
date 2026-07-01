"""
Extension Initialization
Handles initialization of Flask extensions
"""

from flask import Flask
from .core import db, bcrypt, login_manager, csrf, limiter, cache, jwt


def init_extensions(app: Flask) -> None:
    """
    Initialize all Flask extensions
    
    Args:
        app: Flask application instance
    """
    # Initialize database
    db.init_app(app)
    
    # Initialize bcrypt
    bcrypt.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Initialize cache
    cache.init_app(app)
    
    # Initialize JWT
    jwt.init_app(app)


def init_migrations(app: Flask) -> None:
    """
    Initialize database migrations
    
    Args:
        app: Flask application instance
    """
    from flask_migrate import Migrate
    migrate = Migrate()
    migrate.init_app(app, db)


def init_login_manager(app: Flask) -> None:
    """
    Configure login manager and user loader
    
    Args:
        app: Flask application instance
    """
    from app.main.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        try:
            # User.id is UUID, so we need to filter by id
            return User.query.filter_by(id=user_id).first()
        except (ValueError, TypeError):
            return None
