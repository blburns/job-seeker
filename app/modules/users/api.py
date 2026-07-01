"""
User Management API endpoints
RESTful API for user administration and profile management
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions.core import db
from app.main.models import User, Role, Group
from app.utils.security import validate_password_strength, validate_email_format, sanitize_input

logger = logging.getLogger(__name__)

users_api_bp = Blueprint('users_api', __name__, url_prefix='/api/users')


@users_api_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    """Get or update current user profile"""
    try:
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'user': {
                    'id': str(current_user.id),
                    'username': current_user.username,
                    'email': current_user.email,
                    'firstname': current_user.firstname,
                    'lastname': current_user.lastname,
                    'display_name': current_user.display_name,
                    'is_admin': current_user.is_admin,
                    'is_superadmin': current_user.is_superadmin,
                    'email_verified': current_user.email_verified,
                    'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
                    'last_activity': current_user.last_activity.isoformat() if current_user.last_activity else None,
                    'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
                    'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None
                }
            }), 200
        
        elif request.method == 'PUT':
            data = request.get_json() or {}
            
            # Get form data
            firstname = sanitize_input(data.get('firstname', '').strip(), 64)
            lastname = sanitize_input(data.get('lastname', '').strip(), 64)
            display_name = sanitize_input(data.get('display_name', '').strip(), 64)
            email = sanitize_input(data.get('email', '').strip().lower(), 120)
            
            # Validate email if changed
            if email != current_user.email:
                if not validate_email_format(email):
                    return jsonify({
                        'status': 'error',
                        'message': 'Please enter a valid email address'
                    }), 400
                
                # Check if email already exists
                if User.query.filter(User.email == email, User.id != current_user.id).first():
                    return jsonify({
                        'status': 'error',
                        'message': 'Email already exists'
                    }), 400
                
                current_user.email = email
                current_user.email_verified = False
            
            # Update profile fields
            current_user.firstname = firstname
            current_user.lastname = lastname
            current_user.display_name = display_name or f"{firstname} {lastname}".strip()
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Profile updated successfully',
                'user': {
                    'id': str(current_user.id),
                    'username': current_user.username,
                    'email': current_user.email,
                    'firstname': current_user.firstname,
                    'lastname': current_user.lastname,
                    'display_name': current_user.display_name,
                    'email_verified': current_user.email_verified
                }
            }), 200
    
    except Exception as e:
        logger.exception('Error in API profile')
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@users_api_bp.route('/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password"""
    try:
        data = request.get_json() or {}
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            return jsonify({
                'status': 'error',
                'message': 'Current password is incorrect'
            }), 400
        
        # Validate new password
        if new_password != confirm_password:
            return jsonify({
                'status': 'error',
                'message': 'New passwords do not match'
            }), 400
        
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200
    
    except Exception as e:
        logger.exception('Error in API change password')
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@users_api_bp.route('/list')
@login_required
def api_list_users():
    """List all users (admin only)"""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Admin privileges required.'
            }), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = User.query
        
        if search:
            search_filter = or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.firstname.ilike(f'%{search}%'),
                User.lastname.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(User.created_at.desc())
        
        # Paginate results
        users_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users = []
        for user in users_paginated.items:
            users.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'display_name': user.display_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_superadmin': user.is_superadmin,
                'email_verified': user.email_verified,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            'status': 'success',
            'users': users,
            'pagination': {
                'page': users_paginated.page,
                'pages': users_paginated.pages,
                'per_page': users_paginated.per_page,
                'total': users_paginated.total,
                'has_next': users_paginated.has_next,
                'has_prev': users_paginated.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.exception('Error in API list users')
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@users_api_bp.route('/datatable')
@login_required
def api_users_datatable():
    """Flat list of users for Vuexy DataTable (admin only, client-side paging)."""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            return jsonify({'message': 'Access denied'}), 403

        users = User.query.order_by(User.created_at.desc()).all()

        def serialize_user(user: User):
            # Map boolean status to numeric code expected by app-user-list.js
            # 1 = Pending, 2 = Active, 3 = Inactive
            status = 2 if user.is_active else 3

            # Derive a simple role string for the badge column
            role_label = 'User'
            if user.roles:
                first_role = user.roles[0]
                role_label = first_role.display_name or first_role.name or 'User'
            elif user.is_superadmin:
                role_label = 'Super Admin'
            elif user.is_admin:
                role_label = 'Admin'

            full_name = user.get_full_name()

            return {
                'id': str(user.id),
                'full_name': full_name,
                'email': user.email,
                'avatar': None,  # let JS fall back to initials avatar
                'role': role_label,
                'current_plan': 'Basic',
                'billing': 'Current',
                'status': status,
            }

        data = [serialize_user(u) for u in users]
        # DataTables in app-user-list.js uses a flat array (no wrapper key)
        return jsonify(data), 200

    except Exception:
        logger.exception('Error in API users datatable')
        return jsonify({'message': 'Internal server error'}), 500


@users_api_bp.route('/<uuid:user_id>')
@login_required
def api_get_user(user_id):
    """Get user details (admin only)"""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Admin privileges required.'
            }), 403
        
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'display_name': user.display_name,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_superadmin': user.is_superadmin,
                'email_verified': user.email_verified,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'last_activity': user.last_activity.isoformat() if user.last_activity else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        }), 200
    
    except Exception as e:
        logger.exception('Error in API get user')
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
