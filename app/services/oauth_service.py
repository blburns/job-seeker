"""
OAuth Service
Handles OAuth authentication with Google, Microsoft, and GitHub
"""

from flask import current_app, url_for
import logging

logger = logging.getLogger(__name__)

# Try to import Authlib, make it optional
try:
    from authlib.integrations.flask_client import OAuth
    AUTHLIB_AVAILABLE = True
    oauth = OAuth()
except ImportError:
    AUTHLIB_AVAILABLE = False
    oauth = None
    logger.warning("Authlib not installed - OAuth features will be disabled. Install with: pip install Authlib")


class OAuthService:
    """Service for managing OAuth providers"""
    
    def __init__(self, app=None):
        self.oauth = oauth
        self.enabled = AUTHLIB_AVAILABLE
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize OAuth with Flask app
        
        Args:
            app: Flask application instance
        """
        if not AUTHLIB_AVAILABLE:
            logger.warning("OAuth service disabled - Authlib not installed")
            return
        
        # Initialize OAuth
        self.oauth.init_app(app)
        
        # Register Google OAuth
        if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
            self.oauth.register(
                name='google',
                client_id=app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
            logger.info("Google OAuth provider registered")
        else:
            logger.warning("Google OAuth not configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")
        
        # Register Microsoft OAuth
        if app.config.get('MICROSOFT_CLIENT_ID') and app.config.get('MICROSOFT_CLIENT_SECRET'):
            self.oauth.register(
                name='microsoft',
                client_id=app.config.get('MICROSOFT_CLIENT_ID'),
                client_secret=app.config.get('MICROSOFT_CLIENT_SECRET'),
                authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                authorize_params=None,
                access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
                access_token_params=None,
                refresh_token_url=None,
                redirect_uri=None,
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
            logger.info("Microsoft OAuth provider registered")
        else:
            logger.warning("Microsoft OAuth not configured - missing MICROSOFT_CLIENT_ID or MICROSOFT_CLIENT_SECRET")
        
        # Register GitHub OAuth
        if app.config.get('GITHUB_CLIENT_ID') and app.config.get('GITHUB_CLIENT_SECRET'):
            self.oauth.register(
                name='github',
                client_id=app.config.get('GITHUB_CLIENT_ID'),
                client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
                authorize_url='https://github.com/login/oauth/authorize',
                authorize_params=None,
                access_token_url='https://github.com/login/oauth/access_token',
                access_token_params=None,
                refresh_token_url=None,
                redirect_uri=None,
                client_kwargs={
                    'scope': 'user:email'
                }
            )
            logger.info("GitHub OAuth provider registered")
        else:
            logger.warning("GitHub OAuth not configured - missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET")
        
        logger.info("OAuth service initialized")
    
    def get_provider(self, provider_name):
        """
        Get OAuth provider client
        
        Args:
            provider_name: Name of provider (google, microsoft, github)
        
        Returns:
            OAuth client or None
        """
        if not AUTHLIB_AVAILABLE:
            return None
        
        try:
            return getattr(self.oauth, provider_name)
        except AttributeError:
            logger.error(f"OAuth provider '{provider_name}' not registered")
            return None
    
    def is_provider_configured(self, provider_name):
        """
        Check if OAuth provider is configured
        
        Args:
            provider_name: Name of provider (google, microsoft, github)
        
        Returns:
            bool: True if provider is configured
        """
        if not AUTHLIB_AVAILABLE:
            return False
        
        return self.get_provider(provider_name) is not None
    
    @staticmethod
    def get_redirect_uri(provider_name):
        """
        Get OAuth callback redirect URI
        
        Args:
            provider_name: Name of provider (google, microsoft, github)
        
        Returns:
            str: Full callback URL
        """
        return url_for(f'auth.oauth_callback', provider=provider_name, _external=True)
    
    @staticmethod
    def normalize_user_info(provider, user_info):
        """
        Normalize user info from different OAuth providers
        
        Args:
            provider: Provider name (google, microsoft, github)
            user_info: Raw user info from provider
        
        Returns:
            dict: Normalized user info with keys: id, email, name, picture
        """
        if provider == 'google':
            return {
                'id': user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False)
            }
        
        elif provider == 'microsoft':
            return {
                'id': user_info.get('id') or user_info.get('sub'),
                'email': user_info.get('email') or user_info.get('userPrincipalName'),
                'name': user_info.get('displayName') or user_info.get('name'),
                'picture': None,  # Microsoft doesn't provide profile picture in basic scope
                'email_verified': True  # Microsoft emails are verified
            }
        
        elif provider == 'github':
            return {
                'id': str(user_info.get('id')),
                'email': user_info.get('email'),
                'name': user_info.get('name') or user_info.get('login'),
                'picture': user_info.get('avatar_url'),
                'email_verified': True  # GitHub emails are verified
            }
        
        else:
            # Generic normalization
            return {
                'id': user_info.get('id') or user_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture') or user_info.get('avatar_url'),
                'email_verified': user_info.get('email_verified', False)
            }


# Global OAuth service instance
if AUTHLIB_AVAILABLE:
    oauth_service = OAuthService()
else:
    from app.services.oauth_service_stub import oauth_service_stub
    oauth_service = oauth_service_stub
