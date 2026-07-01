"""
RBAC Decorators
Permission checking decorators for route protection
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


def permission_required(permission, redirect_to='main.index', api_mode=False):
    """
    Decorator to require specific permission for a route
    
    Args:
        permission: Permission name (e.g., 'users.view')
        redirect_to: Route to redirect to if permission denied (default: 'main.index')
        api_mode: If True, return JSON response instead of redirect (default: False)
    
    Usage:
        @permission_required('users.create')
        def create_user():
            ...
        
        @permission_required('users.view', api_mode=True)
        def api_get_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check permission
            if not current_user.has_permission(permission):
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (missing permission: {permission})")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Permission denied', 'required_permission': permission}), 403
                
                flash(f'You do not have permission to access this resource. Required permission: {permission}', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def any_permission_required(*permissions, redirect_to='main.index', api_mode=False):
    """
    Decorator to require ANY of the specified permissions
    
    Args:
        *permissions: Permission names (e.g., 'users.view', 'users.create')
        redirect_to: Route to redirect to if permission denied
        api_mode: If True, return JSON response instead of redirect
    
    Usage:
        @any_permission_required('users.view', 'users.create')
        def user_page():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has any of the permissions
            has_any = any(current_user.has_permission(perm) for perm in permissions)
            
            if not has_any:
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (missing any of: {permissions})")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Permission denied', 'required_permissions': list(permissions)}), 403
                
                flash(f'You do not have permission to access this resource', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def all_permissions_required(*permissions, redirect_to='main.index', api_mode=False):
    """
    Decorator to require ALL of the specified permissions
    
    Args:
        *permissions: Permission names (e.g., 'users.view', 'users.update')
        redirect_to: Route to redirect to if permission denied
        api_mode: If True, return JSON response instead of redirect
    
    Usage:
        @all_permissions_required('users.view', 'users.update')
        def edit_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has all permissions
            missing_permissions = [perm for perm in permissions if not current_user.has_permission(perm)]
            
            if missing_permissions:
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (missing: {missing_permissions})")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Permission denied', 'missing_permissions': missing_permissions}), 403
                
                flash(f'You do not have all required permissions to access this resource', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role_name, redirect_to='main.index', api_mode=False):
    """
    Decorator to require specific role for a route
    
    Args:
        role_name: Role name (e.g., 'admin', 'manager')
        redirect_to: Route to redirect to if role not found
        api_mode: If True, return JSON response instead of redirect
    
    Usage:
        @role_required('admin')
        def admin_panel():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check role
            if not current_user.has_role(role_name):
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (missing role: {role_name})")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Role required', 'required_role': role_name}), 403
                
                flash(f'You must have the {role_name} role to access this resource', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(redirect_to='main.index', api_mode=False):
    """
    Decorator to require admin status
    
    Args:
        redirect_to: Route to redirect to if not admin
        api_mode: If True, return JSON response instead of redirect
    
    Usage:
        @admin_required()
        def admin_dashboard():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check admin status
            if not (current_user.is_admin or current_user.is_superadmin):
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (not admin)")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Admin access required'}), 403
                
                flash('You must be an administrator to access this resource', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def superadmin_required(redirect_to='main.index', api_mode=False):
    """
    Decorator to require superadmin status
    
    Args:
        redirect_to: Route to redirect to if not superadmin
        api_mode: If True, return JSON response instead of redirect
    
    Usage:
        @superadmin_required()
        def system_settings():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_mode or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check superadmin status
            if not current_user.is_superadmin:
                logger.warning(f"User {current_user.username} denied access to {request.endpoint} (not superadmin)")
                
                if api_mode or request.is_json:
                    return jsonify({'error': 'Superadmin access required'}), 403
                
                flash('You must be a superadministrator to access this resource', 'danger')
                return redirect(url_for(redirect_to))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Convenience aliases
requires_permission = permission_required
requires_role = role_required
requires_admin = admin_required
requires_superadmin = superadmin_required
