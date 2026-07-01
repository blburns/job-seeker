"""Resume module blueprint."""

from flask import Blueprint

resume_bp = Blueprint('resume', __name__, url_prefix='/resume')

from . import routes  # noqa: E402, F401
from .api import resume_api_bp  # noqa: E402, F401
