"""
OAuth Service Stub
Used when Authlib is not installed
"""

import logging

logger = logging.getLogger(__name__)


class OAuthServiceStub:
    """Stub OAuth service when Authlib is not available"""
    
    def __init__(self, app=None):
        self.enabled = False
        logger.info("OAuth service disabled - Authlib not installed. Install with: pip install Authlib")
    
    def init_app(self, app):
        """Initialize stub (does nothing)"""
        pass
    
    def get_provider(self, provider_name):
        """Returns None - no providers available"""
        return None
    
    def is_provider_configured(self, provider_name):
        """Returns False - OAuth not available"""
        return False
    
    @staticmethod
    def get_redirect_uri(provider_name):
        """Returns empty string"""
        return ""
    
    @staticmethod
    def normalize_user_info(provider, user_info):
        """Returns empty dict"""
        return {}


# Global stub instance
oauth_service_stub = OAuthServiceStub()
