"""Applications module blueprint."""

from flask import Blueprint

applications_bp = Blueprint('applications', __name__, url_prefix='/applications')

from . import routes  # noqa: E402, F401
from .api import applications_api_bp  # noqa: E402, F401
