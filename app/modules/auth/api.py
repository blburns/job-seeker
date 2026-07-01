"""
Authentication API endpoints for enterprise boilerplate application
RESTful API for authentication operations
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app.extensions.core import db
from app.main.models import User
from app.utils.security import validate_password_strength, validate_email_format, sanitize_input

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')


@auth_api_bp.route('/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    try:
        data = request.get_json() or {}
        username_or_email = sanitize_input(data.get('username', ''), 120)
        password = data.get('password')
        
        if not username_or_email or not password:
            return jsonify({
                'status': 'error', 
                'message': 'Username/email and password are required'
            }), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            # Check if account is locked out
            if user.is_locked_out():
                return jsonify({
                    'status': 'error', 
                    'message': 'Account is temporarily locked due to multiple failed login attempts'
                }), 423
            
            # Check if account is active
            if not user.is_active:
                return jsonify({
                    'status': 'error', 
                    'message': 'Account is deactivated'
                }), 403
            
            # Successful login - update user activity
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            user.reset_failed_login()
            db.session.commit()
            
            login_user(user)
            
            return jsonify({
                'status': 'success',
                'user': {
                    'user_uuid': user.user_uuid,
                    'username': user.username,
                    'email': user.email,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                    'display_name': user.display_name,
                    'is_admin': user.is_admin,
                    'is_superadmin': user.is_superadmin,
                    'email_verified': user.email_verified
                }
            }), 200
        
        else:
            # Failed login - increment failed attempts
            if user:
                user.increment_failed_login()
                db.session.commit()
            
            return jsonify({
                'status': 'error', 
                'message': 'Invalid credentials'
            }), 401
    
    except Exception as e:
        logger.exception('Error in API login')
        db.session.rollback()
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500


@auth_api_bp.route('/register', methods=['POST'])
def api_register():
    """API endpoint for user registration"""
    try:
        data = request.get_json() or {}
        username = sanitize_input(data.get('username', '').strip(), 64)
        email = sanitize_input(data.get('email', '').strip().lower(), 120)
        password = data.get('password')
        firstname = sanitize_input(data.get('firstname', '').strip(), 64)
        lastname = sanitize_input(data.get('lastname', '').strip(), 64)
        
        # Validation
        if not all([username, email, password]):
            return jsonify({
                'status': 'error', 
                'message': 'Username, email, and password are required'
            }), 400
        
        # Username validation
        if len(username) < 3 or len(username) > 64:
            return jsonify({
                'status': 'error', 
                'message': 'Username must be between 3 and 64 characters'
            }), 400
        
        # Email validation
        if not validate_email_format(email):
            return jsonify({
                'status': 'error', 
                'message': 'Please enter a valid email address'
            }), 400
        
        # Password validation
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'status': 'error', 
                'message': message
            }), 400
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'status': 'error', 
                'message': 'Username already exists'
            }), 400
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'status': 'error', 
                'message': 'Email already exists'
            }), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            firstname=firstname,
            lastname=lastname,
            display_name=f"{firstname} {lastname}".strip() if firstname or lastname else username
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'user': {
                'user_uuid': user.user_uuid,
                'username': user.username,
                'email': user.email,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'display_name': user.display_name
            }
        }), 201
    
    except Exception as e:
        logger.exception('Error in API register')
        db.session.rollback()
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500


@auth_api_bp.route('/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint for user logout"""
    try:
        logout_user()
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        logger.exception('Error in API logout')
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500


@auth_api_bp.route('/me', methods=['GET'])
@login_required
def api_me():
    """API endpoint to get current user information"""
    try:
        return jsonify({
            'status': 'success',
            'user': {
                'user_uuid': current_user.user_uuid,
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
                'created_at': current_user.created_at.isoformat() if current_user.created_at else None
            }
        }), 200
    except Exception as e:
        logger.exception('Error in API me')
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500


@auth_api_bp.route('/forgot-password', methods=['POST'])
def api_forgot_password():
    """API endpoint for password reset request"""
    try:
        data = request.get_json() or {}
        email = sanitize_input(data.get('email', '').strip().lower(), 120)
        
        if not email or not validate_email_format(email):
            return jsonify({
                'status': 'error', 
                'message': 'Please enter a valid email address'
            }), 400
        
        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            # Generate password reset token
            from app.utils.security import generate_secure_token
            user.password_reset_token = generate_secure_token(32)
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # TODO: Send password reset email
            logger.info(f"Password reset token generated for user {user.username}")
        
        # Always return success for security
        return jsonify({
            'status': 'success',
            'message': 'If an account with that email exists, a password reset link has been sent'
        }), 200
    
    except Exception as e:
        logger.exception('Error in API forgot password')
        db.session.rollback()
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500


@auth_api_bp.route('/reset-password', methods=['POST'])
def api_reset_password():
    """API endpoint for password reset with token"""
    try:
        data = request.get_json() or {}
        token = data.get('token')
        password = data.get('password')
        
        if not token or not password:
            return jsonify({
                'status': 'error', 
                'message': 'Token and password are required'
            }), 400
        
        user = User.query.filter_by(password_reset_token=token).first()
        
        if not user or not user.password_reset_expires or datetime.utcnow() > user.password_reset_expires:
            return jsonify({
                'status': 'error', 
                'message': 'Invalid or expired password reset token'
            }), 400
        
        # Password validation
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'status': 'error', 
                'message': message
            }), 400
        
        # Update password and clear reset token
        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.reset_failed_login()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Password reset successful'
        }), 200
    
    except Exception as e:
        logger.exception('Error in API reset password')
        db.session.rollback()
        return jsonify({
            'status': 'error', 
            'message': 'Internal server error'
        }), 500
