"""
Admin Module
Administrative interface for system management
"""

from flask import Blueprint

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes
from . import routes
