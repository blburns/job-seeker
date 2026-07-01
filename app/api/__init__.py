"""
API Package
RESTful API framework with versioning, request/response handling, and documentation
"""

from flask import Blueprint
from flask_restx import Api
from flask_cors import CORS
from .v1 import api_v1_bp
from .middleware import init_api_middleware
from .documentation import init_api_documentation

def init_api(app):
    """Initialize API components"""
    # Enable CORS for API endpoints
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # Initialize API middleware
    init_api_middleware(app)
    
    # Initialize API documentation
    init_api_documentation(app)
    
    # Register API blueprints
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    print("✅ API Infrastructure initialized")

__all__ = ['init_api', 'api_v1_bp']
