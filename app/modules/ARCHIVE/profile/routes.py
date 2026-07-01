"""
Profile module routes
Public profiles, campaigns, projects, teams, and works
"""

import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create profile blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/')
@login_required
def index():
    """Profile index"""
    return redirect(url_for('profile.public', username=current_user.username))


@profile_bp.route('/<username>')
def public(username):
    """Public profile view"""
    return render_template('modules/profile/public.html', username=username)


@profile_bp.route('/activity')
@login_required
def activity():
    """Profile activity"""
    return render_template('modules/profile/activity.html')


@profile_bp.route('/network')
@login_required
def network():
    """Profile network"""
    return render_template('modules/profile/network.html')


@profile_bp.route('/teams')
@login_required
def teams():
    """Profile teams"""
    return render_template('modules/profile/teams.html')


@profile_bp.route('/works')
@login_required
def works():
    """Profile works"""
    return render_template('modules/profile/works.html')


@profile_bp.route('/empty')
@login_required
def empty():
    """Empty profile state"""
    return render_template('modules/profile/empty.html')
