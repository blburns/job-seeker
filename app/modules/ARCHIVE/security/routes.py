"""
Security module routes
Security logs, monitoring, and security management
"""

import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create security blueprint
security_bp = Blueprint('security', __name__, url_prefix='/security')


@security_bp.route('/')
@login_required
def index():
    """Security index - redirects to security log"""
    return redirect(url_for('security.security_log'))


@security_bp.route('/security-log')
@login_required
def security_log():
    """Security log view"""
    return render_template('modules/security/security_log.html')
