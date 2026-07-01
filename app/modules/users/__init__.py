# Import blueprints from routes and API files
from app.modules.users.routes import users_bp
from app.modules.users.api import users_api_bp

# Import email preferences routes (registers routes on users_bp)
from app.modules.users import email_preferences_routes  # noqa
