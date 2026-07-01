"""
Template Context Processors
Adds global variables to all templates
"""

from flask import g, current_app
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for version import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from version import get_version, get_phase_info, VERSION_INFO


def init_template_context(app):
    """
    Initialize template context processors
    
    Args:
        app: Flask application instance
    """
    
    @app.template_filter('date')
    def date_filter(value, format_string='%Y-%m-%d'):
        """
        Format a date/datetime object using strftime format string.
        
        Usage in templates:
            {{ some_date|date('%Y-%m-%d') }}
            {{ some_date|date('%B %d, %Y') }}
            {{ some_date|date('%Y') }}
        
        Args:
            value: datetime object, date object, or string
            format_string: strftime format string (default: '%Y-%m-%d')
        
        Returns:
            Formatted date string or empty string if value is None/invalid
        """
        if value is None:
            return ''
        
        # If it's already a string, try to parse it
        if isinstance(value, str):
            try:
                # Try common datetime formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S.%f']:
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If we can't parse it, return as-is or empty
                    return value if value else ''
            except Exception:
                return value if value else ''
        
        # Handle datetime and date objects
        if isinstance(value, datetime):
            try:
                return value.strftime(format_string)
            except (ValueError, AttributeError):
                return ''
        elif hasattr(value, 'strftime'):
            # Handle date objects
            try:
                return value.strftime(format_string)
            except (ValueError, AttributeError):
                return ''
        else:
            return str(value) if value else ''
    
    @app.template_filter('number_format')
    def number_format_filter(value, decimals=0):
        """
        Format a number with thousands separator.
        
        Usage in templates:
            {{ 1000|number_format }}  -> "1,000"
            {{ 1234.56|number_format(2) }}  -> "1,234.56"
        
        Args:
            value: Number to format
            decimals: Number of decimal places (default: 0)
        
        Returns:
            Formatted number string
        """
        if value is None:
            return '0'
        
        try:
            if decimals > 0:
                return f"{float(value):,.{decimals}f}"
            else:
                return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)
    
    @app.context_processor
    def inject_app_config():
        """Inject application configuration into templates"""
        return {
            'config': current_app.config,
            'app_name': current_app.config.get('APP_NAME', 'Application'),
            'company_name': current_app.config.get('COMPANY_NAME', 'Your Company'),
            'app_version': get_version(),
            'version_info': VERSION_INFO,
            'phase_info': get_phase_info(),
        }
    
    @app.context_processor
    def inject_user():
        """Inject current user into templates"""
        from flask_login import current_user
        return {
            'current_user': current_user,
            'user': current_user,
        }
    
    @app.context_processor
    def inject_utilities():
        """Inject utility functions into templates"""
        from flask import url_for, has_request_context
        
        def safe_url_for(endpoint, **values):
            """Safely build URL for endpoint, returns '#' if endpoint doesn't exist"""
            if not endpoint:
                return '#'
            try:
                if has_request_context():
                    return url_for(endpoint, **values)
                else:
                    return '#'
            except Exception:
                return '#'
        
        def get_user_display_name(user):
            """Get user display name safely"""
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                return 'Guest'
            try:
                if hasattr(user, 'get_full_name'):
                    name = user.get_full_name()
                    if name:
                        return name
            except Exception:
                pass
            try:
                if hasattr(user, 'username'):
                    return user.username
            except Exception:
                pass
            try:
                if hasattr(user, 'email'):
                    return user.email.split('@')[0] if '@' in user.email else user.email
            except Exception:
                pass
            return 'User'
        
        def get_user_email(user):
            """Get user email safely"""
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                return ''
            try:
                if hasattr(user, 'email'):
                    return user.email
            except Exception:
                pass
            return ''
        
        def get_current_year():
            """Get current year as integer"""
            return datetime.now().year
        
        return {
            'len': len,
            'enumerate': enumerate,
            'zip': zip,
            'range': range,
            'safe_url_for': safe_url_for,
            'get_user_display_name': get_user_display_name,
            'get_user_email': get_user_email,
            'get_current_year': get_current_year,
        }
    
    @app.context_processor
    def inject_request_endpoint():
        """Inject current request endpoint safely for sidebar active state."""
        from flask import has_request_context, request
        endpoint = ''
        if has_request_context() and request:
            endpoint = getattr(request, 'endpoint', None) or ''
        return {'current_request_endpoint': endpoint}

    @app.context_processor
    def inject_modules():
        """Inject module configuration into templates"""
        from flask_login import current_user
        
        # Get modules configuration
        from config.modules import MODULES, ICONS, COLOR_CLASSES, get_visible_modules, get_modules_by_section, MENU_SECTIONS
        
        # Get modules visible to current user
        visible_modules = []
        if current_user.is_authenticated:
            visible_modules = get_visible_modules(current_user)
        else:
            # If not authenticated, only show dashboard
            visible_modules = [m for m in MODULES if m['name'] == 'overview']
        
        # Get modules organized by section
        modules_by_section = {}
        if current_user.is_authenticated:
            modules_by_section = get_modules_by_section(current_user)
        else:
            # If not authenticated, only show dashboard
            modules_by_section = {'job_seeker': [m for m in MODULES if m['name'] == 'overview']}
        
        # Check if user has access to any module (for showing/hiding launcher button)
        has_module_access = len([m for m in visible_modules if m['name'] != 'overview']) > 0
        
        # Only expose the intended sidebar sections (avoids duplicate/extra "Users" or other sections)
        allowed_section_names = ('dashboards', 'job_seeker', 'apps', 'pages', 'account', 'management', 'developer')
        menu_sections = [s for s in MENU_SECTIONS if s.get('name') in allowed_section_names]
        
        return {
            'modules': visible_modules,
            'modules_by_section': modules_by_section,
            'menu_sections': menu_sections,
            'module_icons': ICONS,
            'module_colors': COLOR_CLASSES,
            'has_module_access': has_module_access
        }