"""Jobs module blueprint."""

from flask import Blueprint

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

from . import routes  # noqa: E402, F401
from .api import jobs_api_bp  # noqa: E402, F401
