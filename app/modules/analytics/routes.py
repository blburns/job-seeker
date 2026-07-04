"""Analytics dashboard routes."""

import logging

from flask import jsonify, render_template
from flask_login import current_user, login_required

from app.services.analytics_service import analytics_service
from . import analytics_bp

logger = logging.getLogger(__name__)


@analytics_bp.route('/')
@login_required
def dashboard():
    data = analytics_service.dashboard_data(current_user.id)
    return render_template('modules/analytics/dashboard.html', stats=data)


@analytics_bp.route('/api/summary')
@login_required
def api_summary():
    return jsonify(analytics_service.dashboard_data(current_user.id))
