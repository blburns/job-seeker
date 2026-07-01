"""
CSRF Configuration
Comprehensive CSRF protection setup with advanced features
"""

import logging
from flask import Flask, request, jsonify, current_app
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import current_user
from functools import wraps

logger = logging.getLogger(__name__)


def init_csrf_config(app: Flask) -> None:
    """
    Initialize comprehensive CSRF configuration
    
    Args:
        app: Flask application instance
    """
    # CSRF is already initialized in core.py
    # Configure additional CSRF settings
    
    # Set CSRF token expiration time (1 hour)
    app.config.setdefault('WTF_CSRF_TIME_LIMIT', 3600)
    
    # Enable CSRF protection
    app.config.setdefault('WTF_CSRF_ENABLED', True)
    
    # Set CSRF secret key (should be different from Flask secret)
    app.config.setdefault('WTF_CSRF_SECRET_KEY', app.config.get('SECRET_KEY'))
    
    # Configure CSRF error handling
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF errors with appropriate responses"""
        logger.warning(f'CSRF error: {e.description} from IP: {request.remote_addr}')
        
        # Return JSON response for API requests
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'CSRF token missing or invalid',
                'message': 'Please refresh the page and try again',
                'code': 'CSRF_ERROR'
            }), 400
        
        # Return HTML response for web requests
        from flask import render_template
        return render_template('errors/csrf.html', error=e), 400
    
    # Add CSRF token to template context
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into all templates"""
        from flask_wtf.csrf import generate_csrf
        return {'csrf_token': generate_csrf()}
    
    logger.info('CSRF protection configured successfully')


def csrf_exempt(f):
    """
    Decorator to exempt a view from CSRF protection
    
    Args:
        f: Function to exempt from CSRF
        
    Returns:
        Decorated function
    """
    f.csrf_exempt = True
    return f


def csrf_required(f):
    """
    Decorator to explicitly require CSRF protection
    
    Args:
        f: Function to require CSRF for
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CSRF is handled automatically by Flask-WTF
        # This decorator is mainly for documentation purposes
        return f(*args, **kwargs)
    
    decorated_function.csrf_required = True
    return decorated_function


def validate_csrf_token():
    """
    Validate CSRF token manually
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        from flask_wtf.csrf import validate_csrf
        validate_csrf(request.form.get('csrf_token'))
        return True
    except Exception as e:
        logger.warning(f'CSRF validation failed: {e}')
        return False


def get_csrf_token():
    """
    Get current CSRF token
    
    Returns:
        str: CSRF token
    """
    from flask_wtf.csrf import generate_csrf
    return generate_csrf()


def csrf_protect_api(f):
    """
    Decorator for API endpoints that need CSRF protection
    
    Args:
        f: API function to protect
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if CSRF token is provided in headers
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return jsonify({
                'error': 'CSRF token required',
                'message': 'Include X-CSRF-Token header',
                'code': 'CSRF_TOKEN_MISSING'
            }), 400
        
        # Validate CSRF token
        try:
            from flask_wtf.csrf import validate_csrf
            validate_csrf(csrf_token)
        except Exception as e:
            logger.warning(f'CSRF validation failed for API: {e}')
            return jsonify({
                'error': 'Invalid CSRF token',
                'message': 'CSRF token is invalid or expired',
                'code': 'CSRF_TOKEN_INVALID'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def csrf_protect_ajax(f):
    """
    Decorator for AJAX endpoints that need CSRF protection
    
    Args:
        f: AJAX function to protect
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if CSRF token is provided in form data or headers
        csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return jsonify({
                'error': 'CSRF token required',
                'message': 'Include csrf_token in form data or X-CSRF-Token header',
                'code': 'CSRF_TOKEN_MISSING'
            }), 400
        
        # Validate CSRF token
        try:
            from flask_wtf.csrf import validate_csrf
            validate_csrf(csrf_token)
        except Exception as e:
            logger.warning(f'CSRF validation failed for AJAX: {e}')
            return jsonify({
                'error': 'Invalid CSRF token',
                'message': 'CSRF token is invalid or expired',
                'code': 'CSRF_TOKEN_INVALID'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def setup_csrf_for_forms():
    """
    Setup CSRF protection for forms
    This function can be called to ensure forms have CSRF protection
    """
    # This is handled automatically by Flask-WTF
    # Forms created with FlaskForm automatically include CSRF protection
    pass


def get_csrf_meta_tag():
    """
    Get CSRF token as HTML meta tag
    
    Returns:
        str: HTML meta tag with CSRF token
    """
    token = get_csrf_token()
    return f'<meta name="csrf-token" content="{token}">'


def get_csrf_script():
    """
    Get JavaScript code to setup CSRF token for AJAX requests
    
    Returns:
        str: JavaScript code
    """
    token = get_csrf_token()
    return f'''
    <script>
        // Setup CSRF token for AJAX requests
        window.csrfToken = '{token}';
        
        // Setup jQuery AJAX to include CSRF token
        if (typeof $ !== 'undefined') {{
            $.ajaxSetup({{
                beforeSend: function(xhr, settings) {{
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {{
                        xhr.setRequestHeader("X-CSRF-Token", window.csrfToken);
                    }}
                }}
            }});
        }}
        
        // Setup fetch to include CSRF token
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {{}}) {{
            if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {{
                options.headers = {{
                    ...options.headers,
                    'X-CSRF-Token': window.csrfToken
                }};
            }}
            return originalFetch(url, options);
        }};
    </script>
    '''
