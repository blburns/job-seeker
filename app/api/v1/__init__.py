"""
API v1 Package
Version 1 of the RESTful API
"""

from flask import Blueprint
from flask_restx import Api
from .health import health_ns

# Create API v1 blueprint
api_v1_bp = Blueprint('api_v1', __name__)

# Create API instance with documentation
api_v1 = Api(
    api_v1_bp,
    version='1.0',
    title='Flask Boilerplate API',
    description='RESTful API for Flask Application Boilerplate',
    doc='/docs/',  # Swagger UI documentation
    prefix='/api/v1',
    validate=True,
    catch_all_404s=True
)

# Add namespaces
api_v1.add_namespace(health_ns, path='/health')

__all__ = ['api_v1_bp', 'api_v1']
