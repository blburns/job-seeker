"""
Auth Schema Models
Core authentication and RBAC models (users, roles, groups)
"""

import uuid
from datetime import datetime, timedelta
from flask_login import UserMixin
from app.extensions.core import db
from app.models.base import ID_TYPE
from app.models.schema_utils import db_schema, fk_ref
from app.utils.security import hash_password, check_password

_AUTH_SCHEMA = db_schema('auth')


# Association tables for many-to-many relationships
user_groups = db.Table(
    'user_groups',
    db.Column('user_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'users')), primary_key=True),
    db.Column('group_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'groups')), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    **_AUTH_SCHEMA
)

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'users')), primary_key=True),
    db.Column('role_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles')), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    **_AUTH_SCHEMA
)

group_roles = db.Table(
    'group_roles',
    db.Column('group_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'groups')), primary_key=True),
    db.Column('role_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles')), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    **_AUTH_SCHEMA
)


class Role(db.Model):
    """Role model for RBAC system"""
    __tablename__ = 'roles'
    __table_args__ = _AUTH_SCHEMA
    
    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    permissions = db.Column(db.JSON, nullable=True)
    priority = db.Column(db.Integer, default=0)
    is_system_role = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    groups = db.relationship('Group', secondary=group_roles, back_populates='roles')
    permission_list = db.relationship('Permission', secondary='role_permissions', back_populates='roles', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission_name):
        """Check if role has a specific permission"""
        # Check in permission_list (new system)
        from app.models.rbac import Permission
        perm = Permission.get_by_name(permission_name)
        if perm and perm in self.permission_list.all():
            return True
        
        # Fallback to JSON permissions (legacy)
        if self.permissions and permission_name in self.permissions:
            return True
        
        return False
    
    def add_permission(self, permission):
        """Add a permission to this role"""
        if permission not in self.permission_list.all():
            self.permission_list.append(permission)
    
    def remove_permission(self, permission):
        """Remove a permission from this role"""
        if permission in self.permission_list.all():
            self.permission_list.remove(permission)
    
    def get_all_permissions(self):
        """Get all permission names for this role (including inherited)"""
        permissions = set()
        
        # Add direct permissions
        for perm in self.permission_list.all():
            if perm.is_active:
                permissions.add(perm.name)
        
        # Add legacy JSON permissions
        if self.permissions:
            permissions.update(self.permissions)
        
        # TODO: Add inherited permissions from role hierarchy
        
        return list(permissions)
    
    def to_dict(self):
        """Convert role to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'permissions': self.permissions,
            'priority': self.priority,
            'is_system_role': self.is_system_role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Group(db.Model):
    """Group model for organizing users"""
    __tablename__ = 'groups'
    __table_args__ = _AUTH_SCHEMA
    
    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_system_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', secondary=user_groups, back_populates='groups')
    roles = db.relationship('Role', secondary=group_roles, back_populates='groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'is_system_group': self.is_system_group,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FailedLogin(db.Model):
    """Model to track failed login attempts"""
    __tablename__ = 'failed_logins'
    __table_args__ = _AUTH_SCHEMA
    
    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    username_or_email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(64), nullable=True) # e.g., 'invalid_password', 'user_not_found', 'locked_out'

    def __repr__(self):
        return f'<FailedLogin {self.username_or_email} at {self.attempted_at}>'


class User(UserMixin, db.Model):
    """Enhanced User model with comprehensive security features"""
    __tablename__ = 'users'
    __table_args__ = _AUTH_SCHEMA
    
    # Primary identification
    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_expires = db.Column(db.DateTime, nullable=True)
    
    # Password reset
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    
    # Activity tracking
    last_login = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    
    # Security features
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    lockout_until = db.Column(db.DateTime, nullable=True)
    
    # Two-Factor Authentication
    totp_secret = db.Column(db.String(32), nullable=True)  # Base32 encoded secret
    totp_enabled = db.Column(db.Boolean, default=False)
    totp_enabled_at = db.Column(db.DateTime, nullable=True)
    backup_codes = db.Column(db.JSON, nullable=True)  # List of hashed backup codes
    
    # Profile information
    firstname = db.Column(db.String(64), nullable=True)
    lastname = db.Column(db.String(64), nullable=True)
    display_name = db.Column(db.String(64), nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    
    # Extended profile information
    organization = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    state = db.Column(db.String(64), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    language = db.Column(db.String(10), nullable=True)
    timezone = db.Column(db.String(64), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    groups = db.relationship('Group', secondary=user_groups, back_populates='users')
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    
    def get_id(self):
        """Override Flask-Login's get_id method to return id"""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password: str) -> None:
        """Set password hash"""
        self.password_hash = hash_password(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        if self.firstname and self.lastname:
            return f"{self.firstname} {self.lastname}"
        return self.display_name or self.username

    @property
    def photo_url(self):
        """URL for profile photo (avatar). Use in request context (e.g. templates)."""
        if not self.avatar_path:
            return None
        from flask import url_for
        return url_for('static', filename=self.avatar_path)
    
    def is_locked_out(self) -> bool:
        """Check if account is locked out"""
        if self.lockout_until:
            return datetime.utcnow() < self.lockout_until
        return False
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.lockout_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.lockout_until = None
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission (RBAC)"""
        # Super admins have all permissions
        if self.is_superadmin:
            return True
        
        # Admins have all permissions (can be configured differently)
        if self.is_admin:
            return True
        
        # Check role assignments (new system with expiration)
        from app.models.rbac import UserRoleAssignment
        active_assignments = UserRoleAssignment.query.filter_by(
            user_id=self.id,
            is_active=True
        ).all()
        
        for assignment in active_assignments:
            if assignment.is_valid and assignment.role.has_permission(permission):
                return True
        
        # Fallback to old system for backward compatibility
        # Parse permission string (e.g., 'user.view' -> module='user', action='view')
        if '.' not in permission:
            return False
        
        module, action = permission.split('.', 1)
        
        # Map old permission names to new ones for backward compatibility
        module_mapping = {
            'contact': 'contacts',
            'document': 'documents',
            'user': 'users',
            'role': 'roles',
            'group': 'groups',
            'email_relay': 'email_relay',
            'email': 'email',
            'analytics': 'analytics',
            'tenant': 'tenants',
            'organization': 'organizations',
            'org': 'organizations',
            'account': 'accounts',
        }
        
        # Map action names for backward compatibility and consistency
        action_mapping = {
            'read': 'view',
            'edit': 'update',
        }
        
        # Apply action mapping if needed
        action = action_mapping.get(action, action)
        
        # Use mapped module name if it exists, otherwise use original
        module = module_mapping.get(module, module)
        
        # Check direct role permissions (legacy JSON system)
        for role in self.roles:
            if role.is_active and role.permissions:
                permissions = role.permissions if isinstance(role.permissions, dict) else {}
                if module in permissions and action in permissions[module]:
                    return True
        
        # Check group role permissions
        for group in self.groups:
            if group.is_active:
                for role in group.roles:
                    if role.is_active and role.permissions:
                        permissions = role.permissions if isinstance(role.permissions, dict) else {}
                        if module in permissions and action in permissions[module]:
                            return True
        
        return False
    
    def get_all_permissions(self):
        """Get all permission names for this user"""
        if self.is_superadmin or self.is_admin:
            return ['*']  # All permissions
        
        permissions = set()
        
        # Get permissions from role assignments (new system)
        from app.models.rbac import UserRoleAssignment
        active_assignments = UserRoleAssignment.query.filter_by(
            user_id=self.id,
            is_active=True
        ).all()
        
        for assignment in active_assignments:
            if assignment.is_valid:
                permissions.update(assignment.role.get_all_permissions())
        
        # Get permissions from direct roles (legacy)
        for role in self.roles:
            if role.is_active:
                permissions.update(role.get_all_permissions())
        
        # Get permissions from group roles
        for group in self.groups:
            if group.is_active:
                for role in group.roles:
                    if role.is_active:
                        permissions.update(role.get_all_permissions())
        
        return list(permissions)
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        # Check direct roles
        for role in self.roles:
            if role.name == role_name and role.is_active:
                return True
        
        # Check role assignments (new system)
        from app.models.rbac import UserRoleAssignment
        active_assignments = UserRoleAssignment.query.filter_by(
            user_id=self.id,
            is_active=True
        ).all()
        
        for assignment in active_assignments:
            if assignment.is_valid and assignment.role.name == role_name:
                return True
        
        # Check group roles
        for group in self.groups:
            if group.is_active:
                for role in group.roles:
                    if role.name == role_name and role.is_active:
                        return True
        
        return False
    
    def is_module_visible(self, module_name: str) -> bool:
        """Check if a module should be visible in the modules launcher for this user"""
        from config.modules import MODULES
        
        # Find module configuration
        module_config = next((m for m in MODULES if m['name'] == module_name), None)
        
        if not module_config:
            return False
        
        # Overview is always visible
        if module_config['name'] == 'overview':
            return True
        
        # Admin and Super Admin see all modules by default
        if self.is_superadmin or self.is_admin:
            return True
        
        # For regular users, check permission if required
        permission = module_config.get('permission')
        if permission:
            return self.has_permission(permission)
        
        return False
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'is_superadmin': self.is_superadmin,
            'email_verified': self.email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'display_name': self.display_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
