"""
Logging Configuration
Handles application logging setup
"""

import logging
import os
from flask import Flask


def init_logging_config(app: Flask) -> None:
    """
    Initialize logging configuration
    
    Args:
        app: Flask application instance
    """
    if not app.debug and not app.testing:
        # Configure file logging for production
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
