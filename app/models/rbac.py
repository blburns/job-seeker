"""
RBAC (Role-Based Access Control) Models
Enhanced permission system with granular access control
"""

import uuid
from datetime import datetime
from app.extensions.core import db
from app.models.base import ID_TYPE
from app.models.schema_utils import db_schema, fk_ref, auth_table_args

_AUTH_SCHEMA = db_schema('auth')


# Association table for role-permission many-to-many relationship
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles'), ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', ID_TYPE, db.ForeignKey(fk_ref('auth', 'permissions'), ondelete='CASCADE'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow),
    **_AUTH_SCHEMA
)


class Permission(db.Model):
    """Permission model for granular access control"""
    __tablename__ = 'permissions'
    __table_args__ = _AUTH_SCHEMA
    
    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    
    # Permission identification
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)  # e.g., 'users.create'
    display_name = db.Column(db.String(100), nullable=False)  # e.g., 'Create Users'
    description = db.Column(db.Text, nullable=True)
    
    # Permission organization
    module = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'users', 'products', 'orders'
    category = db.Column(db.String(50), nullable=True)  # e.g., 'management', 'reporting'
    
    # Permission metadata
    is_system = db.Column(db.Boolean, default=False)  # System permissions cannot be deleted
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)  # For ordering in UI
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = db.relationship('Role', secondary='role_permissions', back_populates='permission_list')
    
    def __repr__(self):
        return f'<Permission {self.name}>'
    
    def to_dict(self):
        """Convert permission to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'module': self.module,
            'category': self.category,
            'is_system': self.is_system,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_name(cls, name):
        """Get permission by name"""
        return cls.query.filter_by(name=name, is_active=True).first()
    
    @classmethod
    def get_by_module(cls, module):
        """Get all permissions for a module"""
        return cls.query.filter_by(module=module, is_active=True).order_by(cls.priority, cls.name).all()
    
    @classmethod
    def get_all_modules(cls):
        """Get list of all unique modules"""
        return db.session.query(cls.module).distinct().order_by(cls.module).all()


class UserRoleAssignment(db.Model):
    """
    Enhanced user-role assignment with expiration and audit
    Replaces the simple user_roles association table
    """
    __tablename__ = 'user_role_assignments'

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    
    user_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='CASCADE'), nullable=False, index=True)
    role_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles'), ondelete='CASCADE'), nullable=False, index=True)
    
    # Assignment metadata
    assigned_by = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='SET NULL'), nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='SET NULL'), nullable=True)
    revoke_reason = db.Column(db.Text, nullable=True)
    
    # Audit
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='role_assignments')
    role = db.relationship('Role', backref='user_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by])
    revoker = db.relationship('User', foreign_keys=[revoked_by])
    
    # Unique constraint
    __table_args__ = auth_table_args(
        db.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )
    
    def __repr__(self):
        return f'<UserRoleAssignment user={self.user_id} role={self.role_id}>'
    
    def to_dict(self):
        """Convert assignment to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'role_id': str(self.role_id),
            'assigned_by': str(self.assigned_by) if self.assigned_by else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked_by': str(self.revoked_by) if self.revoked_by else None,
            'revoke_reason': self.revoke_reason,
            'notes': self.notes
        }
    
    @property
    def is_expired(self):
        """Check if assignment is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if assignment is currently valid"""
        return self.is_active and not self.is_expired and not self.revoked_at
    
    def revoke(self, revoked_by_id, reason=None):
        """Revoke this role assignment"""
        self.is_active = False
        self.revoked_at = datetime.utcnow()
        self.revoked_by = revoked_by_id
        self.revoke_reason = reason


class RoleHierarchy(db.Model):
    """
    Role hierarchy for role inheritance
    Allows roles to inherit permissions from parent roles
    """
    __tablename__ = 'role_hierarchy'

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    parent_role_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles'), ondelete='CASCADE'), nullable=False, index=True)
    child_role_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'roles'), ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='SET NULL'), nullable=True)

    parent_role = db.relationship('Role', foreign_keys=[parent_role_id], backref='child_hierarchies')
    child_role = db.relationship('Role', foreign_keys=[child_role_id], backref='parent_hierarchies')
    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = auth_table_args(
        db.UniqueConstraint('parent_role_id', 'child_role_id', name='uq_role_hierarchy'),
    )
    
    def __repr__(self):
        return f'<RoleHierarchy parent={self.parent_role_id} child={self.child_role_id}>'
    
    @classmethod
    def get_parent_roles(cls, role_id):
        """Get all parent roles for a given role"""
        return cls.query.filter_by(child_role_id=role_id).all()
    
    @classmethod
    def get_child_roles(cls, role_id):
        """Get all child roles for a given role"""
        return cls.query.filter_by(parent_role_id=role_id).all()
