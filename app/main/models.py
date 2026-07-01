"""
Enhanced User Models for Enterprise Boilerplate
Comprehensive user management with security features and RBAC support

NOTE: Models have been moved to app/models/auth.py with schema support.
This file is kept for backward compatibility but imports from the new location.
"""

# Import from new models location
from app.models.auth import User, Role, Group, user_groups, user_roles, group_roles

# Re-export for backward compatibility
__all__ = ['User', 'Role', 'Group', 'user_groups', 'user_roles', 'group_roles']
