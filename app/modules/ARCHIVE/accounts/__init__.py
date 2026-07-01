# Import blueprints from routes and API files
from app.modules.accounts.routes import accounts_bp
from app.modules.accounts.api import accounts_api_bp

__all__ = ['accounts_bp', 'accounts_api_bp']
