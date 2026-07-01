"""
API Middleware
Request/response handling, authentication, rate limiting, and error handling
"""

from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = None

def init_api_middleware(app):
    """Initialize API middleware components"""
    global limiter
    
    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["10000 per hour", "1000 per minute"]
    )
    limiter.init_app(app)
    
    # Register middleware functions
    app.before_request(before_request)
    app.after_request(after_request)
    
    print("✅ API Middleware initialized")

def before_request():
    """Process requests before they reach endpoints"""
    # Start request timer
    g.start_time = time.time()
    
    # Log API requests
    if request.path.startswith('/api/'):
        logger.info(f"API Request: {request.method} {request.path} from {request.remote_addr}")
    
    # Add CORS headers for preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        return response

def after_request(response):
    """Process responses after they leave endpoints"""
    # Add request timing
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
    
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
    
    return response

def require_auth(f):
    """Decorator to require authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        try:
            verify_jwt_in_request()
            g.current_user_id = get_jwt_identity()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required', 'message': str(e)}), 401
    
    return decorated_function

def require_permission(permission):
    """Decorator to require specific permission for API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would require an auth service - simplified for now
            if not hasattr(g, 'current_user_id'):
                return jsonify({'error': 'Authentication required'}), 401
            
            # Permission check would go here
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_error_handler(error):
    """Global API error handler"""
    response = {
        'error': True,
        'message': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if hasattr(error, 'code'):
        response['code'] = error.code
    
    return jsonify(response), getattr(error, 'code', 500)

def validate_json_content_type(f):
    """Decorator to validate JSON content type for POST/PUT requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
        return f(*args, **kwargs)
    return decorated_function

def paginate_results(results, page=1, per_page=20, max_per_page=100):
    """Paginate query results"""
    if per_page > max_per_page:
        per_page = max_per_page
    
    paginated = results.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return {
        'items': [item.to_dict() for item in paginated.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'pages': paginated.pages,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev,
            'next_num': paginated.next_num,
            'prev_num': paginated.prev_num
        }
    }

__all__ = ['limiter', 'require_auth', 'require_permission', 'api_error_handler', 'validate_json_content_type', 'paginate_results']
