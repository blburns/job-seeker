"""
User Management Routes
Comprehensive user administration, profile management, and user operations
"""

import logging
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app, Blueprint, session
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app.extensions.core import db
from app.main.models import User, Role, Group
from app.models.session import UserSession
from app.utils.security import validate_password_strength, validate_email_format, sanitize_input

logger = logging.getLogger(__name__)

# Create users blueprint
users_bp = Blueprint('users', __name__, url_prefix='/users')

# Profile photo upload
ALLOWED_AVATAR_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_AVATAR_SIZE = 800 * 1024  # 800KB


@users_bp.route('/')
@login_required
def index():
    """Redirect to users dashboard"""
    return redirect(url_for('users.dashboard'))


@users_bp.route('/dashboard')
@login_required
def dashboard():
    """Users module dashboard"""
    try:
        # Get user statistics with safe queries
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Get role statistics with safe handling
        roles = []
        role_stats = {}
        try:
            roles = Role.query.all()
            for role in roles:
                try:
                    role_stats[role.name] = len(role.users) if hasattr(role, 'users') and role.users else 0
                except:
                    role_stats[role.name] = 0
        except Exception as e:
            logger.warning(f"Error getting roles: {e}")
            roles = []
            role_stats = {}
        
        # Get group statistics with safe handling
        groups = []
        group_stats = {}
        try:
            groups = Group.query.all()
            for group in groups:
                try:
                    group_stats[group.name] = len(group.users) if hasattr(group, 'users') and group.users else 0
                except:
                    group_stats[group.name] = 0
        except Exception as e:
            logger.warning(f"Error getting groups: {e}")
            groups = []
            group_stats = {}
        
        return render_template('modules/users/dashboard.html',
                            total_users=total_users,
                            active_users=active_users,
                            admin_users=admin_users,
                            recent_users=recent_users,
                            roles=roles,
                            groups=groups,
                            role_stats=role_stats,
                            group_stats=group_stats)
    
    except Exception as e:
        logger.exception('Error in users dashboard')
        flash('Error loading users dashboard', 'danger')
        return render_template('errors/500.html'), 500


@users_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        return render_template('modules/users/profile/profile.html', user=current_user)
    except Exception as e:
        logger.exception('Error in profile route')
        return render_template('errors/500.html'), 500


@users_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    try:
        if request.method == 'POST':
            # Handle avatar upload
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename:
                ext = (secure_filename(avatar_file.filename) or '').rsplit('.', 1)[-1].lower()
                if ext not in ALLOWED_AVATAR_EXTENSIONS:
                    flash('Invalid image type. Use JPG, PNG, or GIF.', 'warning')
                else:
                    data = avatar_file.read()
                    if len(data) > MAX_AVATAR_SIZE:
                        flash('Image too large. Max size is 800KB.', 'warning')
                    else:
                        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
                        os.makedirs(upload_dir, exist_ok=True)
                        filename = f"{current_user.id}.{ext}"
                        filepath = os.path.join(upload_dir, filename)
                        try:
                            with open(filepath, 'wb') as f:
                                f.write(data)
                            current_user.avatar_path = os.path.join('uploads', 'avatars', filename).replace('\\', '/')
                            db.session.commit()
                        except OSError as e:
                            logger.warning('Avatar save failed: %s', e)
                            flash('Could not save photo. Please try again.', 'warning')

            # Get form data
            firstname = sanitize_input(request.form.get('firstname', '').strip(), 64)
            lastname = sanitize_input(request.form.get('lastname', '').strip(), 64)
            display_name = sanitize_input(request.form.get('display_name', '').strip(), 64)
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            
            # Validate email if changed
            if email != current_user.email:
                if not validate_email_format(email):
                    flash('Please enter a valid email address', 'warning')
                    return render_template('modules/users/profile/edit_profile.html', user=current_user)
                
                # Check if email already exists
                if User.query.filter(User.email == email, User.id != current_user.id).first():
                    flash('Email already exists', 'warning')
                    return render_template('modules/users/profile/edit_profile.html', user=current_user)
                
                current_user.email = email
                current_user.email_verified = False  # Require re-verification
            
            # Update profile fields
            current_user.firstname = firstname
            current_user.lastname = lastname
            current_user.display_name = display_name or f"{firstname} {lastname}".strip()
            current_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Profile updated successfully', 'success')
            return redirect(url_for('users.profile'))
        
        return render_template('modules/users/profile/edit_profile.html', user=current_user)
    
    except Exception as e:
        logger.exception('Error in edit_profile route')
        db.session.rollback()
        flash('An error occurred while updating your profile', 'danger')
        return render_template('modules/users/profile/edit_profile.html', user=current_user), 500


@users_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'warning')
                return render_template('modules/users/profile/change_password.html')
            
            # Validate new password
            if new_password != confirm_password:
                flash('New passwords do not match', 'warning')
                return render_template('modules/users/profile/change_password.html')
            
            is_valid, message = validate_password_strength(new_password)
            if not is_valid:
                flash(message, 'warning')
                return render_template('modules/users/profile/change_password.html')
            
            # Update password
            current_user.set_password(new_password)
            current_user.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('users.profile'))
        
        return render_template('modules/users/profile/change_password.html')
    
    except Exception as e:
        logger.exception('Error in change_password route')
        db.session.rollback()
        flash('An error occurred while changing your password', 'danger')
        return render_template('modules/users/profile/change_password.html'), 500


@users_bp.route('/profile/teams')
@login_required
def teams():
    """User profile - Teams page"""
    return render_template('modules/users/profile/teams.html', user=current_user)


@users_bp.route('/profile/projects')
@login_required
def projects():
    """User profile - Projects page"""
    return render_template('modules/users/profile/projects.html', user=current_user)


@users_bp.route('/profile/connections')
@login_required
def connections():
    """User profile - Connections page"""
    return render_template('modules/users/profile/connections.html', user=current_user)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create new user (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        if request.method == 'POST':
            # Get form data
            username = sanitize_input(request.form.get('username', '').strip(), 64)
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            password = request.form.get('password', '')
            firstname = sanitize_input(request.form.get('firstname', '').strip(), 64)
            lastname = sanitize_input(request.form.get('lastname', '').strip(), 64)
            display_name = sanitize_input(request.form.get('display_name', '').strip(), 64)
            is_active = request.form.get('is_active') == 'on'
            is_admin = request.form.get('is_admin') == 'on'
            is_superadmin = request.form.get('is_superadmin') == 'on'
            
            # Validate inputs
            if len(username) < 3 or len(username) > 64:
                flash('Username must be between 3 and 64 characters', 'warning')
                return render_template('modules/users/create.html')
            
            if not validate_email_format(email):
                flash('Please enter a valid email address', 'warning')
                return render_template('modules/users/create.html')
            
            is_valid, message = validate_password_strength(password)
            if not is_valid:
                flash(message, 'warning')
                return render_template('modules/users/create.html')
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'warning')
                return render_template('modules/users/create.html')
            
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'warning')
                return render_template('modules/users/create.html')
            
            # Create user
            user = User(
                username=username,
                email=email,
                firstname=firstname,
                lastname=lastname,
                display_name=display_name or f"{firstname} {lastname}".strip() or username,
                is_active=is_active,
                is_admin=is_admin,
                is_superadmin=is_superadmin
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('User created successfully', 'success')
            return redirect(url_for('users.view_user', user_id=user.id))
        
        return render_template('modules/users/create.html')
    
    except Exception as e:
        logger.exception('Error in create_user route')
        db.session.rollback()
        flash('An error occurred while creating user', 'danger')
        return render_template('modules/users/create.html'), 500


@users_bp.route('/list')
@login_required
def list_users():
    """List users page (admin only, Vuexy DataTable frontend)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))

        # High-level stats for cards (DataTable handles listing via API)
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        pending_users = total_users - active_users

        return render_template(
            'modules/users/list.html',
            total_users=total_users,
            active_users=active_users,
            admin_users=admin_users,
            pending_users=pending_users,
        )
    
    except Exception as e:
        logger.exception('Error in list_users route')
        return render_template('errors/500.html'), 500


@users_bp.route('/permissions')
@login_required
def list_permissions():
    """List all permissions (Permissions page)."""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))

        # Extract unique permissions from all roles
        permissions_dict = {}
        roles_with_permissions = Role.query.filter(Role.permissions.isnot(None)).all()
        
        for role in roles_with_permissions:
            if role.permissions and isinstance(role.permissions, dict):
                for module, actions in role.permissions.items():
                    if isinstance(actions, list):
                        for action in actions:
                            perm_name = f"{module}.{action}"
                            if perm_name not in permissions_dict:
                                permissions_dict[perm_name] = {
                                    'name': perm_name,
                                    'roles': [],
                                    'created_date': role.created_at
                                }
                            if role not in permissions_dict[perm_name]['roles']:
                                permissions_dict[perm_name]['roles'].append(role)
                    elif isinstance(actions, dict):
                        for action in actions.keys():
                            perm_name = f"{module}.{action}"
                            if perm_name not in permissions_dict:
                                permissions_dict[perm_name] = {
                                    'name': perm_name,
                                    'roles': [],
                                    'created_date': role.created_at
                                }
                            if role not in permissions_dict[perm_name]['roles']:
                                permissions_dict[perm_name]['roles'].append(role)
        
        # Convert to list and sort by name
        permissions = sorted(permissions_dict.values(), key=lambda x: x['name'])
        
        # Handle form submission
        if request.method == 'POST':
            permission_name = request.form.get('permission_name', '').strip()
            is_core = request.form.get('is_core') == 'on'
            permission_id = request.form.get('permission_id')
            
            if permission_id:
                # Edit permission (would need to update all roles that use it)
                flash('Permission editing functionality coming soon', 'info')
            else:
                # Add permission (would need to create a permission entry)
                flash('Permission creation functionality coming soon', 'info')
            
            return redirect(url_for('users.list_permissions'))

        return render_template('modules/users/access/permissions_list.html', permissions=permissions)
    
    except Exception as e:
        logger.exception('Error in list_permissions route')
        flash('An error occurred while loading permissions', 'danger')
        return redirect(url_for('users.dashboard'))


@users_bp.route('/roles-permissions')
@login_required
def list_roles():
    """List all roles and permissions (Roles & Permissions list page)."""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()

        query = Role.query
        if search:
            query = query.filter(
                or_(
                    Role.name.ilike(f'%{search}%'),
                    Role.display_name.ilike(f'%{search}%'),
                    Role.description.ilike(f'%{search}%'),
                )
            )
        query = query.order_by(Role.name.asc())
        roles = query.paginate(page=page, per_page=per_page, error_out=False)

        total_roles = Role.query.count()
        active_roles = Role.query.filter_by(is_active=True).count()
        system_roles = Role.query.filter_by(is_system_role=True).count()
        custom_roles = Role.query.filter_by(is_system_role=False).count()

        # Get all users with their roles for the table
        users = User.query.filter(User.roles.any()).all()

        return render_template(
            'modules/users/access/roles_permissions_list.html',
            roles=roles,
            users=users,
            search=search,
            total_roles=total_roles,
            active_roles=active_roles,
            system_roles=system_roles,
            custom_roles=custom_roles,
        )
    except Exception as e:
        logger.exception('Error in list_roles route')
        flash('An error occurred while loading roles', 'danger')
        return redirect(url_for('users.dashboard'))


@users_bp.route('/view/<uuid:user_id>')
@login_required
def view_user(user_id):
    """View user details (admin only) - canonical account view."""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/view/account.html', user=user)
    
    except Exception as e:
        logger.exception('Error in view_user route')
        return render_template('errors/500.html'), 500


@users_bp.route('/view/<uuid:user_id>/account')
@login_required
def view_user_account(user_id):
    """Explicit account tab view (mirrors /view/<id>)."""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))

        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/view/account.html', user=user)

    except Exception:
        logger.exception('Error in view_user_account route')
        return render_template('errors/500.html'), 500


@users_bp.route('/view/<uuid:user_id>/security', methods=['GET', 'POST'])
@login_required
def view_user_security(user_id):
    """View user security settings (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        
        # Handle password change form submission
        if request.method == 'POST' and 'change_password' in request.form:
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not new_password or not confirm_password:
                flash('Please fill in all password fields', 'warning')
                return render_template('modules/users/view/security.html', user=user)
            
            if new_password != confirm_password:
                flash('Passwords do not match', 'warning')
                return render_template('modules/users/view/security.html', user=user)
            
            # Validate password strength
            validation_result = validate_password_strength(new_password)
            if not validation_result['valid']:
                flash(validation_result['message'], 'warning')
                return render_template('modules/users/view/security.html', user=user)
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('users.view_user_security', user_id=user_id))
        
        # Placeholder for recent devices (would come from session tracking in production)
        recent_devices = [
            {
                'browser': 'Chrome on Windows',
                'device': 'HP Spectre 360',
                'location': 'Switzerland',
                'last_activity': user.last_activity or user.last_login or user.created_at
            },
            {
                'browser': 'Chrome on iPhone',
                'device': 'iPhone 12x',
                'location': 'Australia',
                'last_activity': (user.last_activity or user.last_login or user.created_at) - timedelta(days=3) if user.last_activity else None
            },
            {
                'browser': 'Chrome on Android',
                'device': 'Oneplus 9 Pro',
                'location': 'Dubai',
                'last_activity': (user.last_activity or user.last_login or user.created_at) - timedelta(days=4) if user.last_activity else None
            },
            {
                'browser': 'Chrome on MacOS',
                'device': 'Apple iMac',
                'location': 'India',
                'last_activity': (user.last_activity or user.last_login or user.created_at) - timedelta(days=5) if user.last_activity else None
            },
        ]
        
        return render_template('modules/users/view/security.html', user=user, recent_devices=recent_devices)
    
    except Exception as e:
        logger.exception('Error in view_user_security route')
        return render_template('errors/500.html'), 500


@users_bp.route('/view/<uuid:user_id>/billing')
@login_required
def view_user_billing(user_id):
    """View user billing & plans (admin only)"""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/view/billing.html', user=user)
    
    except Exception as e:
        logger.exception('Error in view_user_billing route')
        return render_template('errors/500.html'), 500


@users_bp.route('/view/<uuid:user_id>/notifications')
@login_required
def view_user_notifications(user_id):
    """View user notifications (admin only)"""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/view/notifications.html', user=user)
    
    except Exception as e:
        logger.exception('Error in view_user_notifications route')
        return render_template('errors/500.html'), 500


@users_bp.route('/view/<uuid:user_id>/connections')
@login_required
def view_user_connections(user_id):
    """View user connections (admin only)"""
    try:
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/view/connections.html', user=user)
    
    except Exception as e:
        logger.exception('Error in view_user_connections route')
        return render_template('errors/500.html'), 500


@users_bp.route('/edit/<uuid:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        
        if request.method == 'POST':
            # Get form data
            username = sanitize_input(request.form.get('username', '').strip(), 64)
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            firstname = sanitize_input(request.form.get('firstname', '').strip(), 64)
            lastname = sanitize_input(request.form.get('lastname', '').strip(), 64)
            display_name = sanitize_input(request.form.get('display_name', '').strip(), 64)
            is_active = request.form.get('is_active') == 'on'
            is_admin = request.form.get('is_admin') == 'on'
            is_superadmin = request.form.get('is_superadmin') == 'on'
            
            # Validate username if changed
            if username != user.username:
                if len(username) < 3 or len(username) > 64:
                    flash('Username must be between 3 and 64 characters', 'warning')
                    return render_template('modules/users/edit.html', user=user)
                
                if User.query.filter(User.username == username, User.id != user.id).first():
                    flash('Username already exists', 'warning')
                    return render_template('modules/users/edit.html', user=user)
                
                user.username = username
            
            # Validate email if changed
            if email != user.email:
                if not validate_email_format(email):
                    flash('Please enter a valid email address', 'warning')
                    return render_template('modules/users/edit.html', user=user)
                
                if User.query.filter(User.email == email, User.id != user.id).first():
                    flash('Email already exists', 'warning')
                    return render_template('modules/users/edit.html', user=user)
                
                user.email = email
                user.email_verified = False
            
            # Update user fields
            user.firstname = firstname
            user.lastname = lastname
            user.display_name = display_name or f"{firstname} {lastname}".strip()
            user.is_active = is_active
            user.is_admin = is_admin
            user.is_superadmin = is_superadmin
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('users.view_user', user_id=user.id))
        
        return render_template('modules/users/edit.html', user=user)
    
    except Exception as e:
        logger.exception('Error in edit_user route')
        db.session.rollback()
        flash('An error occurred while updating the user', 'danger')
        try:
            user = User.query.filter_by(id=user_id).first()
            return render_template('modules/users/edit.html', user=user), 500
        except:
            return redirect(url_for('users.list_users')), 500


@users_bp.route('/status/<uuid:user_id>')
@login_required
def toggle_user_status(user_id):
    """Toggle user active status (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        
        # Prevent deactivating superadmin
        if user.is_superadmin and current_user.id != user.id:
            flash('Cannot deactivate superadmin account', 'warning')
            return redirect(url_for('users.view_user', user_id=user.id))
        
        user.is_active = not user.is_active
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {status} successfully', 'success')
        return redirect(url_for('users.view_user', user_id=user.id))
    
    except Exception as e:
        logger.exception('Error in toggle_user_status route')
        db.session.rollback()
        flash('An error occurred while updating user status', 'danger')
        return redirect(url_for('users.view_user', user_id=user_id)), 500


@users_bp.route('/activity/<uuid:user_id>')
@login_required
def user_activity(user_id):
    """View user activity log (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        user = User.query.filter_by(id=user_id).first_or_404()
        return render_template('modules/users/activity.html', user=user)
    
    except Exception as e:
        logger.exception('Error in user_activity route')
        return render_template('errors/500.html'), 500


@users_bp.route('/analytics')
@login_required
def user_analytics():
    """User analytics dashboard (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        return render_template('modules/users/analytics.html')
    
    except Exception as e:
        logger.exception('Error in user_analytics route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings')
@login_required
def settings():
    """Redirect to Account tab of account settings"""
    return redirect(url_for('users.settings_account'))


@users_bp.route('/settings/account', methods=['GET', 'POST'])
@login_required
def settings_account():
    """Account Settings - Account tab (current user)"""
    try:
        if request.method == 'POST':
            firstname = request.form.get('firstName', '').strip() or None
            lastname = request.form.get('lastName', '').strip() or None
            organization = request.form.get('organization', '').strip() or None
            phone = request.form.get('phoneNumber', '').strip() or None
            address = request.form.get('address', '').strip() or None
            state = request.form.get('state', '').strip() or None
            zip_code = request.form.get('zipCode', '').strip() or None
            country = request.form.get('country', '').strip() or None
            language = request.form.get('language', '').strip() or None
            timezone = request.form.get('timeZones', '').strip() or None
            currency = request.form.get('currency', '').strip() or None

            current_user.firstname = firstname
            current_user.lastname = lastname
            current_user.organization = organization
            current_user.phone = phone
            current_user.address = address
            current_user.state = state
            current_user.zip_code = zip_code
            current_user.country = country
            current_user.language = language
            current_user.timezone = timezone
            current_user.currency = currency
            
            db.session.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('users.settings_account'))
        return render_template('modules/users/settings/account.html', user=current_user)
    except Exception as e:
        logger.exception('Error in settings_account route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/security', methods=['GET', 'POST'])
@login_required
def settings_security():
    """Account Settings - Security tab (current user)"""
    try:
        from app.services.totp_service import totp_service
        
        # Check if 2FA setup is in progress
        setup_in_progress = session.get('2fa_setup_secret') is not None
        
        return render_template('modules/users/settings/security.html', 
                             user=current_user,
                             setup_in_progress=setup_in_progress)
    except Exception as e:
        logger.exception('Error in settings_security route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/security/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup two-factor authentication"""
    try:
        from app.services.totp_service import totp_service
        from flask import current_app
        
        if request.method == 'POST':
            # Verify the TOTP code
            token = request.form.get('token', '').strip()
            secret = session.get('2fa_setup_secret')
            
            if not secret:
                flash('2FA setup session expired. Please start again.', 'warning')
                return redirect(url_for('users.settings_security'))
            
            if not token or len(token) != 6:
                flash('Please enter a valid 6-digit code', 'warning')
                return render_template('modules/users/settings/2fa_setup.html',
                                     secret=secret,
                                     qr_code=session.get('2fa_setup_qr'))
            
            # Verify the token
            if totp_service.verify_token(secret, token):
                # Generate backup codes
                backup_codes = totp_service.generate_backup_codes(10)
                hashed_codes = [totp_service.hash_backup_code(code) for code in backup_codes]
                
                # Enable 2FA for user
                current_user.totp_secret = secret
                current_user.totp_enabled = True
                current_user.totp_enabled_at = datetime.utcnow()
                current_user.backup_codes = hashed_codes
                db.session.commit()
                
                # Clear setup session
                session.pop('2fa_setup_secret', None)
                session.pop('2fa_setup_qr', None)
                
                # Store backup codes in session for display
                session['2fa_backup_codes'] = backup_codes
                
                flash('Two-factor authentication enabled successfully!', 'success')
                return redirect(url_for('users.show_backup_codes'))
            else:
                flash('Invalid code. Please try again.', 'danger')
                return render_template('modules/users/settings/2fa_setup.html',
                                     secret=secret,
                                     qr_code=session.get('2fa_setup_qr'))
        
        # GET request - generate new secret and QR code
        secret = totp_service.generate_secret()
        app_name = current_app.config.get('APP_NAME', 'Application')
        uri = totp_service.get_totp_uri(secret, current_user.email, app_name)
        qr_code = totp_service.generate_qr_code(uri)
        
        # Store in session
        session['2fa_setup_secret'] = secret
        session['2fa_setup_qr'] = qr_code
        
        return render_template('modules/users/settings/2fa_setup.html',
                             secret=secret,
                             qr_code=qr_code)
    
    except Exception as e:
        logger.exception('Error in setup_2fa route')
        db.session.rollback()
        flash('An error occurred while setting up 2FA', 'danger')
        return redirect(url_for('users.settings_security')), 500


@users_bp.route('/settings/security/2fa/backup-codes')
@login_required
def show_backup_codes():
    """Show backup codes after 2FA setup"""
    try:
        backup_codes = session.get('2fa_backup_codes')
        
        if not backup_codes:
            flash('No backup codes to display', 'warning')
            return redirect(url_for('users.settings_security'))
        
        return render_template('modules/users/settings/2fa_backup_codes.html',
                             backup_codes=backup_codes)
    except Exception as e:
        logger.exception('Error in show_backup_codes route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/security/2fa/backup-codes/confirm', methods=['POST'])
@login_required
def confirm_backup_codes():
    """Confirm user has saved backup codes"""
    try:
        # Clear backup codes from session
        session.pop('2fa_backup_codes', None)
        
        flash('Backup codes confirmed. Keep them in a safe place!', 'success')
        return redirect(url_for('users.settings_security'))
    except Exception as e:
        logger.exception('Error in confirm_backup_codes route')
        return redirect(url_for('users.settings_security')), 500


@users_bp.route('/settings/security/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    """Disable two-factor authentication"""
    try:
        from app.services.totp_service import totp_service
        
        # Verify password before disabling
        password = request.form.get('password', '')
        
        if not current_user.check_password(password):
            flash('Incorrect password. Cannot disable 2FA.', 'danger')
            return redirect(url_for('users.settings_security'))
        
        # Disable 2FA
        current_user.totp_secret = None
        current_user.totp_enabled = False
        current_user.totp_enabled_at = None
        current_user.backup_codes = None
        db.session.commit()
        
        flash('Two-factor authentication has been disabled', 'success')
        return redirect(url_for('users.settings_security'))
    
    except Exception as e:
        logger.exception('Error in disable_2fa route')
        db.session.rollback()
        flash('An error occurred while disabling 2FA', 'danger')
        return redirect(url_for('users.settings_security')), 500


@users_bp.route('/settings/security/2fa/regenerate-backup-codes', methods=['POST'])
@login_required
def regenerate_backup_codes():
    """Regenerate backup codes"""
    try:
        from app.services.totp_service import totp_service
        
        if not current_user.totp_enabled:
            flash('2FA is not enabled', 'warning')
            return redirect(url_for('users.settings_security'))
        
        # Verify password
        password = request.form.get('password', '')
        
        if not current_user.check_password(password):
            flash('Incorrect password. Cannot regenerate backup codes.', 'danger')
            return redirect(url_for('users.settings_security'))
        
        # Generate new backup codes
        backup_codes = totp_service.generate_backup_codes(10)
        hashed_codes = [totp_service.hash_backup_code(code) for code in backup_codes]
        
        # Update user
        current_user.backup_codes = hashed_codes
        db.session.commit()
        
        # Store in session for display
        session['2fa_backup_codes'] = backup_codes
        
        flash('Backup codes regenerated successfully', 'success')
        return redirect(url_for('users.show_backup_codes'))
    
    except Exception as e:
        logger.exception('Error in regenerate_backup_codes route')
        db.session.rollback()
        flash('An error occurred while regenerating backup codes', 'danger')
        return redirect(url_for('users.settings_security')), 500


@users_bp.route('/settings/billing')
@login_required
def settings_billing():
    """Account Settings - Billing & Plans tab (current user)"""
    try:
        return render_template('modules/users/settings/billing.html', user=current_user)
    except Exception as e:
        logger.exception('Error in settings_billing route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/notifications')
@login_required
def settings_notifications():
    """Account Settings - Notifications tab (current user)"""
    try:
        return render_template('modules/users/settings/notifications.html', user=current_user)
    except Exception as e:
        logger.exception('Error in settings_notifications route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/connections')
@login_required
def settings_connections():
    """Account Settings - Connections tab (current user)"""
    try:
        return render_template('modules/users/settings/connections.html', user=current_user)
    except Exception as e:
        logger.exception('Error in settings_connections route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/sessions')
@login_required
def settings_sessions():
    """Account Settings - Active Sessions tab (current user)"""
    try:
        # Get current session token
        current_session_token = session.get('session_token')
        
        # Get all active sessions for current user
        active_sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(UserSession.last_activity.desc()).all()
        
        # Mark current session
        for sess in active_sessions:
            sess.is_current = (sess.session_token == current_session_token)
        
        return render_template('modules/users/settings/sessions.html', 
                             user=current_user, 
                             sessions=active_sessions)
    except Exception as e:
        logger.exception('Error in settings_sessions route')
        return render_template('errors/500.html'), 500


@users_bp.route('/settings/sessions/<uuid:session_id>/revoke', methods=['POST'])
@login_required
def revoke_session(session_id):
    """Revoke a specific session"""
    try:
        user_session = UserSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first_or_404()
        
        # Don't allow revoking current session (use logout instead)
        current_session_token = session.get('session_token')
        if user_session.session_token == current_session_token:
            flash('Cannot revoke current session. Use logout instead.', 'warning')
            return redirect(url_for('users.settings_sessions'))
        
        user_session.revoke()
        db.session.commit()
        
        flash('Session revoked successfully', 'success')
        return redirect(url_for('users.settings_sessions'))
    except Exception as e:
        logger.exception('Error in revoke_session route')
        db.session.rollback()
        flash('An error occurred while revoking the session', 'danger')
        return redirect(url_for('users.settings_sessions')), 500


@users_bp.route('/settings/sessions/revoke-all', methods=['POST'])
@login_required
def revoke_all_sessions():
    """Revoke all sessions except current one"""
    try:
        current_session_token = session.get('session_token')
        current_session = UserSession.query.filter_by(
            session_token=current_session_token
        ).first()
        
        # Revoke all sessions except current
        count = UserSession.revoke_all_user_sessions(
            user_id=current_user.id,
            except_session_id=current_session.id if current_session else None
        )
        
        flash(f'Successfully revoked {count} session(s)', 'success')
        return redirect(url_for('users.settings_sessions'))
    except Exception as e:
        logger.exception('Error in revoke_all_sessions route')
        db.session.rollback()
        flash('An error occurred while revoking sessions', 'danger')
        return redirect(url_for('users.settings_sessions')), 500


@users_bp.route('/status')
@login_required
def status():
    """User status page"""
    try:
        return render_template('modules/users/status.html', user=current_user)
    except Exception as e:
        logger.exception('Error in status route')
        return render_template('errors/500.html'), 500


@users_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_users():
    """Import users from CSV (admin only)"""
    try:
        # Check if user has admin permissions
        if not (current_user.is_admin or current_user.is_superadmin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        
        if request.method == 'POST':
            # Check if file was uploaded
            if 'csv_file' not in request.files:
                flash('No file provided', 'warning')
                return render_template('modules/users/import.html')
            
            file = request.files['csv_file']
            
            if file.filename == '':
                flash('No file selected', 'warning')
                return render_template('modules/users/import.html')
            
            if not file.filename.endswith('.csv'):
                flash('Please upload a CSV file', 'warning')
                return render_template('modules/users/import.html')
            
            flash('Import functionality coming soon', 'info')
            return redirect(url_for('users.list_users'))
        
        return render_template('modules/users/import.html')
    
    except Exception as e:
        logger.exception('Error in import_users route')
        flash('An error occurred while importing users', 'danger')
        return render_template('modules/users/import.html'), 500
