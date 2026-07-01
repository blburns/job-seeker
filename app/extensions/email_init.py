"""
Email Service Initialization
Initialize email service with Flask app
"""

import logging
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


def init_email_service(app):
    """Initialize email service with Flask app"""
    try:
        email_service.init_app(app)
        logger.info("Email service initialized successfully")
    except Exception as e:
        logger.exception(f"Error initializing email service: {e}")
