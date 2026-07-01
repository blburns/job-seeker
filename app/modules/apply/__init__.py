"""Apply module blueprint."""

from flask import Blueprint

apply_bp = Blueprint('apply', __name__, url_prefix='/apply')

from . import routes  # noqa: E402, F401
from .api import apply_api_bp  # noqa: E402, F401
