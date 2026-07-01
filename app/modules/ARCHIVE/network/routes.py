"""
Network module routes
User networking, connections, user cards, and user tables
"""

import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create network blueprint
network_bp = Blueprint('network', __name__, url_prefix='/network')


@network_bp.route('/')
@login_required
def index():
    """Network index - redirects to get started"""
    return redirect(url_for('network.get_started'))


@network_bp.route('/get-started')
@login_required
def get_started():
    """Network get started page"""
    return render_template('modules/network/get_started.html')
