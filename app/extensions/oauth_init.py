"""
OAuth Service Initialization
"""

from app.services.oauth_service import oauth_service


def init_oauth_service(app):
    """
    Initialize OAuth service with Flask app
    
    Args:
        app: Flask application instance
    """
    oauth_service.init_app(app)
