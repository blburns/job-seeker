"""
CRM Module
Customer Relationship Management module
"""

from flask import Blueprint

# Create CRM blueprint
crm_bp = Blueprint('crm', __name__, url_prefix='/crm')

# Import routes to register them
from . import routes

# Import API blueprint
from .api import crm_api_bp

__all__ = ['crm_bp', 'crm_api_bp']
