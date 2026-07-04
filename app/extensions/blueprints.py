"""
Blueprint Registration
Job seeker application blueprints
"""

from flask import Flask
from app.main.routes import main_bp

try:
    from app.modules.auth import auth_bp
    from app.modules.auth.api import auth_api_bp
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

try:
    from app.modules.users import users_bp, users_api_bp
    HAS_USERS = True
except ImportError:
    HAS_USERS = False

try:
    from app.modules.admin import admin_bp
    HAS_ADMIN = True
except ImportError:
    HAS_ADMIN = False

try:
    from app.modules.resume import resume_bp, resume_api_bp
    HAS_RESUME = True
except ImportError:
    HAS_RESUME = False

try:
    from app.modules.jobs import jobs_bp, jobs_api_bp
    HAS_JOBS = True
except ImportError:
    HAS_JOBS = False

try:
    from app.modules.applications import applications_bp, applications_api_bp
    HAS_APPLICATIONS = True
except ImportError:
    HAS_APPLICATIONS = False

try:
    from app.modules.apply import apply_bp, apply_api_bp
    HAS_APPLY = True
except ImportError:
    HAS_APPLY = False

try:
    from app.modules.analytics import analytics_bp
    HAS_ANALYTICS = True
except ImportError:
    HAS_ANALYTICS = False


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    app.register_blueprint(main_bp)

    if HAS_AUTH:
        app.register_blueprint(auth_bp)
        app.register_blueprint(auth_api_bp)

    if HAS_USERS:
        app.register_blueprint(users_bp)
        app.register_blueprint(users_api_bp)

    if HAS_ADMIN:
        app.register_blueprint(admin_bp)

    if HAS_RESUME:
        app.register_blueprint(resume_bp)
        app.register_blueprint(resume_api_bp)

    if HAS_JOBS:
        app.register_blueprint(jobs_bp)
        app.register_blueprint(jobs_api_bp)

    if HAS_APPLICATIONS:
        app.register_blueprint(applications_bp)
        app.register_blueprint(applications_api_bp)

    if HAS_APPLY:
        app.register_blueprint(apply_bp)
        app.register_blueprint(apply_api_bp)

    if HAS_ANALYTICS:
        app.register_blueprint(analytics_bp)
