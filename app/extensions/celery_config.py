"""
Celery Configuration
Async task queue for background jobs
"""

import os
from celery import Celery
from flask import Flask


def make_celery(app: Flask = None) -> Celery:
    """
    Create and configure Celery instance
    
    Args:
        app: Flask application instance
    
    Returns:
        Celery: Configured Celery instance
    """
    celery = Celery(
        app.import_name if app else 'app',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    )
    
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            """Task that runs within Flask application context"""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery


# Celery configuration
celery_config = {
    # Broker settings
    'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Task settings
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    
    # Task execution settings
    'task_track_started': True,
    'task_time_limit': 600,
    'task_soft_time_limit': 540,

    'task_routes': {
        'app.tasks.job_tasks.run_discovery_for_profile': {'queue': 'scraping'},
        'app.tasks.job_tasks.run_all_active_discoveries': {'queue': 'scraping'},
    },
    
    # Task retry settings
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_default_retry_delay': 60,  # 1 minute
    'task_max_retries': 3,
    
    # Result backend settings
    'result_expires': 3600,  # 1 hour
    
    # Worker settings
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 50,
    
    # Beat schedule (for periodic tasks)
    'beat_schedule': {
        'cleanup-expired-sessions': {
            'task': 'app.tasks.maintenance_tasks.cleanup_expired_sessions',
            'schedule': 3600.0,
        },
        'cleanup-expired-role-assignments': {
            'task': 'app.tasks.maintenance_tasks.cleanup_expired_role_assignments',
            'schedule': 3600.0,
        },
        'cleanup-old-email-logs': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_email_logs',
            'schedule': 86400.0,
        },
        'run-active-job-discoveries': {
            'task': 'app.tasks.job_tasks.run_all_active_discoveries',
            'schedule': 21600.0,
        },
        'check-follow-up-reminders': {
            'task': 'app.tasks.job_tasks.check_follow_up_reminders',
            'schedule': 86400.0,
        },
        'check-portal-sessions': {
            'task': 'app.tasks.job_tasks.check_portal_sessions',
            'schedule': 43200.0,
        },
    },
}


def init_celery(app: Flask, celery: Celery) -> Celery:
    """
    Initialize Celery with Flask app configuration
    
    Args:
        app: Flask application instance
        celery: Celery instance
    
    Returns:
        Celery: Configured Celery instance
    """
    celery.conf.update(celery_config)
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        """Task that runs within Flask application context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery
