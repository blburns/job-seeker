"""
Cache Extension
Redis integration and caching strategies for performance optimization
"""

from flask import current_app
from flask_caching import Cache
from typing import Any, Optional, Union
import json
import pickle
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Global cache instance
cache = None

def init_cache(app):
    """Initialize cache system"""
    global cache
    
    # Configure cache based on environment
    if app.config.get('CACHE_TYPE') == 'redis':
        cache_config = {
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
            'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
            'CACHE_KEY_PREFIX': 'flask_boilerplate:',
            'CACHE_REDIS_DB': 0
        }
    else:
        # Fallback to simple cache
        cache_config = {
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300
        }
    
    cache = Cache(app, config=cache_config)
    print("✅ Cache system initialized")

def get_cache() -> Optional[Cache]:
    """Get cache instance"""
    return cache

def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments"""
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, tuple)):
            key_parts.append(','.join(map(str, arg)))
        elif isinstance(arg, dict):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        if value is not None:
            key_parts.append(f"{key}:{value}")
    
    # Create hash for long keys
    key_string = ':'.join(key_parts)
    if len(key_string) > 250:  # Redis key length limit
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:hash:{key_hash}"
    
    return key_string

def cached(timeout: int = 300, key_prefix: str = 'default'):
    """Decorator for caching function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not cache:
                return func(*args, **kwargs)
            
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            try:
                result = cache.get(key)
                if result is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return result
            except Exception as e:
                logger.warning(f"Cache get failed for key {key}: {e}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
                logger.debug(f"Cached result for key: {key}")
                return result
            except Exception as e:
                logger.error(f"Function execution failed: {e}")
                raise
        
        return wrapper
    return decorator

def cache_set(key: str, value: Any, timeout: int = 300) -> bool:
    """Set cache value"""
    if not cache:
        return False
    
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"Cache set failed for key {key}: {e}")
        return False

def cache_get(key: str) -> Any:
    """Get cache value"""
    if not cache:
        return None
    
    try:
        return cache.get(key)
    except Exception as e:
        logger.error(f"Cache get failed for key {key}: {e}")
        return None

def cache_delete(key: str) -> bool:
    """Delete cache value"""
    if not cache:
        return False
    
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete failed for key {key}: {e}")
        return False

def cache_clear() -> bool:
    """Clear all cache"""
    if not cache:
        return False
    
    try:
        cache.clear()
        return True
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        return False

def cache_memoize(timeout: int = 300, key_prefix: str = 'memoize'):
    """Memoization decorator with cache"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not cache:
                return func(*args, **kwargs)
            
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            try:
                result = cache.get(key)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"Cache memoize get failed for key {key}: {e}")
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            try:
                cache.set(key, result, timeout=timeout)
            except Exception as e:
                logger.warning(f"Cache memoize set failed for key {key}: {e}")
            
            return result
        
        return wrapper
    return decorator

def check_cache_health() -> dict:
    """Check cache system health"""
    if not cache:
        return {
            'status': False,
            'message': 'Cache not initialized',
            'type': 'none'
        }
    
    try:
        # Test cache operations
        test_key = 'health_check'
        test_value = 'ok'
        
        # Test set
        cache.set(test_key, test_value, timeout=10)
        
        # Test get
        result = cache.get(test_key)
        
        # Test delete
        cache.delete(test_key)
        
        if result == test_value:
            return {
                'status': True,
                'message': 'Cache is healthy',
                'type': current_app.config.get('CACHE_TYPE', 'unknown')
            }
        else:
            return {
                'status': False,
                'message': 'Cache test failed',
                'type': current_app.config.get('CACHE_TYPE', 'unknown')
            }
            
    except Exception as e:
        return {
            'status': False,
            'message': f'Cache health check failed: {str(e)}',
            'type': current_app.config.get('CACHE_TYPE', 'unknown')
        }

def get_cache_stats() -> dict:
    """Get cache statistics"""
    if not cache:
        return {
            'type': 'none',
            'status': 'not_available'
        }
    
    try:
        # This would typically query Redis INFO command
        # For now, return basic info
        return {
            'type': current_app.config.get('CACHE_TYPE', 'unknown'),
            'status': 'available',
            'default_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
        }
    except Exception as e:
        return {
            'type': current_app.config.get('CACHE_TYPE', 'unknown'),
            'status': 'error',
            'error': str(e)
        }

# Cache strategies
class CacheStrategy:
    """Cache strategy patterns"""
    
    @staticmethod
    def cache_user_data(user_id: str, data: dict, timeout: int = 3600):
        """Cache user-specific data"""
        key = cache_key('user', user_id)
        return cache_set(key, data, timeout)
    
    @staticmethod
    def get_user_data(user_id: str) -> Optional[dict]:
        """Get cached user data"""
        key = cache_key('user', user_id)
        return cache_get(key)
    
    @staticmethod
    def cache_api_response(endpoint: str, params: dict, response: dict, timeout: int = 300):
        """Cache API response"""
        key = cache_key('api', endpoint, **params)
        return cache_set(key, response, timeout)
    
    @staticmethod
    def get_api_response(endpoint: str, params: dict) -> Optional[dict]:
        """Get cached API response"""
        key = cache_key('api', endpoint, **params)
        return cache_get(key)
    
    @staticmethod
    def cache_database_query(query_hash: str, result: Any, timeout: int = 600):
        """Cache database query result"""
        key = cache_key('db_query', query_hash)
        return cache_set(key, result, timeout)
    
    @staticmethod
    def get_database_query(query_hash: str) -> Any:
        """Get cached database query result"""
        key = cache_key('db_query', query_hash)
        return cache_get(key)

__all__ = [
    'init_cache', 'get_cache', 'cache_key', 'cached', 'cache_set', 
    'cache_get', 'cache_delete', 'cache_clear', 'cache_memoize',
    'check_cache_health', 'get_cache_stats', 'CacheStrategy'
]
