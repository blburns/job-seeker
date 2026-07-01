"""
Celery Application
Entry point for Celery worker
"""

import os
from app import create_app
from app.extensions.celery_config import make_celery

# Create Flask app
flask_app = create_app()

# Create Celery app
celery = make_celery(flask_app)

# Import tasks to register them
import app.tasks  # noqa

if __name__ == '__main__':
    celery.start()
