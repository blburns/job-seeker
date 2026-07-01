#!/usr/bin/env python3
"""
Add RBAC (Role-Based Access Control) tables
Creates permissions, role_permissions, user_role_assignments, and role_hierarchy tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db

def add_rbac_tables():
    """Create RBAC tables"""
    app = create_app()
    
    with app.app_context():
        # SQL to create RBAC tables
        sql = """
        -- Create permissions table
        CREATE TABLE IF NOT EXISTS auth.permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            description TEXT,
            module VARCHAR(50) NOT NULL,
            category VARCHAR(50),
            is_system BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create indexes for permissions
        CREATE INDEX IF NOT EXISTS idx_permissions_name ON auth.permissions(name);
        CREATE INDEX IF NOT EXISTS idx_permissions_module ON auth.permissions(module);
        CREATE INDEX IF NOT EXISTS idx_permissions_active ON auth.permissions(is_active);
        
        -- Create role_permissions junction table
        CREATE TABLE IF NOT EXISTS auth.role_permissions (
            role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (role_id, permission_id)
        );
        
        -- Create indexes for role_permissions
        CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON auth.role_permissions(role_id);
        CREATE INDEX IF NOT EXISTS idx_role_permissions_permission ON auth.role_permissions(permission_id);
        
        -- Create user_role_assignments table (enhanced user-role relationship)
        CREATE TABLE IF NOT EXISTS auth.user_role_assignments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            assigned_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
            assigned_at TIMESTAMP DEFAULT NOW() NOT NULL,
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            revoked_at TIMESTAMP,
            revoked_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
            revoke_reason TEXT,
            notes TEXT,
            CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
        );
        
        -- Create indexes for user_role_assignments
        CREATE INDEX IF NOT EXISTS idx_user_role_assignments_user ON auth.user_role_assignments(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_role_assignments_role ON auth.user_role_assignments(role_id);
        CREATE INDEX IF NOT EXISTS idx_user_role_assignments_active ON auth.user_role_assignments(is_active);
        CREATE INDEX IF NOT EXISTS idx_user_role_assignments_expires ON auth.user_role_assignments(expires_at);
        
        -- Create role_hierarchy table (role inheritance)
        CREATE TABLE IF NOT EXISTS auth.role_hierarchy (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            parent_role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            child_role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
            CONSTRAINT uq_role_hierarchy UNIQUE (parent_role_id, child_role_id),
            CONSTRAINT chk_no_self_reference CHECK (parent_role_id != child_role_id)
        );
        
        -- Create indexes for role_hierarchy
        CREATE INDEX IF NOT EXISTS idx_role_hierarchy_parent ON auth.role_hierarchy(parent_role_id);
        CREATE INDEX IF NOT EXISTS idx_role_hierarchy_child ON auth.role_hierarchy(child_role_id);
        """
        
        try:
            # Execute SQL
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ RBAC tables created successfully")
            print("  - auth.permissions")
            print("  - auth.role_permissions")
            print("  - auth.user_role_assignments")
            print("  - auth.role_hierarchy")
            print("✓ Indexes created for all RBAC tables")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating RBAC tables: {e}")
            return False

def seed_default_permissions():
    """Seed default permissions for common modules"""
    app = create_app()
    
    with app.app_context():
        from app.models.rbac import Permission
        
        # Define default permissions
        default_permissions = [
            # User Management
            {'name': 'users.view', 'display_name': 'View Users', 'module': 'users', 'category': 'management', 'description': 'View user list and details'},
            {'name': 'users.create', 'display_name': 'Create Users', 'module': 'users', 'category': 'management', 'description': 'Create new users'},
            {'name': 'users.update', 'display_name': 'Update Users', 'module': 'users', 'category': 'management', 'description': 'Edit user information'},
            {'name': 'users.delete', 'display_name': 'Delete Users', 'module': 'users', 'category': 'management', 'description': 'Delete users'},
            {'name': 'users.activate', 'display_name': 'Activate/Deactivate Users', 'module': 'users', 'category': 'management', 'description': 'Activate or deactivate user accounts'},
            
            # Role Management
            {'name': 'roles.view', 'display_name': 'View Roles', 'module': 'roles', 'category': 'management', 'description': 'View role list and details', 'is_system': True},
            {'name': 'roles.create', 'display_name': 'Create Roles', 'module': 'roles', 'category': 'management', 'description': 'Create new roles', 'is_system': True},
            {'name': 'roles.update', 'display_name': 'Update Roles', 'module': 'roles', 'category': 'management', 'description': 'Edit role information', 'is_system': True},
            {'name': 'roles.delete', 'display_name': 'Delete Roles', 'module': 'roles', 'category': 'management', 'description': 'Delete roles', 'is_system': True},
            {'name': 'roles.assign', 'display_name': 'Assign Roles', 'module': 'roles', 'category': 'management', 'description': 'Assign roles to users', 'is_system': True},
            
            # Permission Management
            {'name': 'permissions.view', 'display_name': 'View Permissions', 'module': 'permissions', 'category': 'management', 'description': 'View permission list', 'is_system': True},
            {'name': 'permissions.manage', 'display_name': 'Manage Permissions', 'module': 'permissions', 'category': 'management', 'description': 'Create and edit permissions', 'is_system': True},
            
            # Group Management
            {'name': 'groups.view', 'display_name': 'View Groups', 'module': 'groups', 'category': 'management', 'description': 'View group list and details'},
            {'name': 'groups.create', 'display_name': 'Create Groups', 'module': 'groups', 'category': 'management', 'description': 'Create new groups'},
            {'name': 'groups.update', 'display_name': 'Update Groups', 'module': 'groups', 'category': 'management', 'description': 'Edit group information'},
            {'name': 'groups.delete', 'display_name': 'Delete Groups', 'module': 'groups', 'category': 'management', 'description': 'Delete groups'},
            
            # Settings
            {'name': 'settings.view', 'display_name': 'View Settings', 'module': 'settings', 'category': 'configuration', 'description': 'View application settings'},
            {'name': 'settings.update', 'display_name': 'Update Settings', 'module': 'settings', 'category': 'configuration', 'description': 'Modify application settings', 'is_system': True},
            
            # Audit Logs
            {'name': 'audit.view', 'display_name': 'View Audit Logs', 'module': 'audit', 'category': 'security', 'description': 'View system audit logs', 'is_system': True},
        ]
        
        try:
            created_count = 0
            for perm_data in default_permissions:
                # Check if permission already exists
                existing = Permission.query.filter_by(name=perm_data['name']).first()
                if not existing:
                    permission = Permission(**perm_data)
                    db.session.add(permission)
                    created_count += 1
            
            db.session.commit()
            print(f"✓ Seeded {created_count} default permissions")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding permissions: {e}")
            return False

if __name__ == '__main__':
    print("Creating RBAC tables...")
    tables_success = add_rbac_tables()
    
    if tables_success:
        print("\nSeeding default permissions...")
        seed_success = seed_default_permissions()
        sys.exit(0 if seed_success else 1)
    else:
        sys.exit(1)
