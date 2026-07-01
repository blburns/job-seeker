#!/usr/bin/env python3
"""
Seed all system permissions
Run this after adding new modules or features

Usage:
    python scripts/seed_permissions.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db
from app.services.rbac_service import rbac_service

# Define all system permissions
SYSTEM_PERMISSIONS = {
    'users': {
        'display_name': 'User Management',
        'permissions': [
            {
                'name': 'users.view',
                'display_name': 'View Users',
                'description': 'View user list and search users'
            },
            {
                'name': 'users.view.details',
                'display_name': 'View User Details',
                'description': 'View detailed user information'
            },
            {
                'name': 'users.create',
                'display_name': 'Create Users',
                'description': 'Create new user accounts'
            },
            {
                'name': 'users.update',
                'display_name': 'Update Users',
                'description': 'Update user information'
            },
            {
                'name': 'users.update.own',
                'display_name': 'Update Own Profile',
                'description': 'Update own profile information only'
            },
            {
                'name': 'users.delete',
                'display_name': 'Delete Users',
                'description': 'Delete user accounts'
            },
            {
                'name': 'users.export',
                'display_name': 'Export Users',
                'description': 'Export user data'
            },
        ]
    },
    'admin': {
        'display_name': 'Administration',
        'permissions': [
            {
                'name': 'admin.access',
                'display_name': 'Access Admin Area',
                'description': 'Access administrative interface'
            },
            {
                'name': 'admin.dashboard.view',
                'display_name': 'View Admin Dashboard',
                'description': 'View admin dashboard and metrics'
            },
            {
                'name': 'admin.monitoring.view',
                'display_name': 'View System Monitoring',
                'description': 'View system health and monitoring'
            },
        ]
    },
    'permissions': {
        'display_name': 'Permission Management',
        'permissions': [
            {
                'name': 'permissions.view',
                'display_name': 'View Permissions',
                'description': 'View permission list'
            },
            {
                'name': 'permissions.create',
                'display_name': 'Create Permissions',
                'description': 'Create new permissions'
            },
            {
                'name': 'permissions.update',
                'display_name': 'Update Permissions',
                'description': 'Update existing permissions'
            },
            {
                'name': 'permissions.delete',
                'display_name': 'Delete Permissions',
                'description': 'Delete permissions'
            },
            {
                'name': 'permissions.manage',
                'display_name': 'Manage Permissions',
                'description': 'Full permission management access'
            },
        ]
    },
    'roles': {
        'display_name': 'Role Management',
        'permissions': [
            {
                'name': 'roles.view',
                'display_name': 'View Roles',
                'description': 'View role list'
            },
            {
                'name': 'roles.create',
                'display_name': 'Create Roles',
                'description': 'Create new roles'
            },
            {
                'name': 'roles.update',
                'display_name': 'Update Roles',
                'description': 'Update existing roles'
            },
            {
                'name': 'roles.delete',
                'display_name': 'Delete Roles',
                'description': 'Delete roles'
            },
            {
                'name': 'roles.assign',
                'display_name': 'Assign Roles',
                'description': 'Assign roles to users'
            },
        ]
    },
    'reports': {
        'display_name': 'Reports',
        'permissions': [
            {
                'name': 'reports.view',
                'display_name': 'View Reports',
                'description': 'View and access reports'
            },
            {
                'name': 'reports.create',
                'display_name': 'Create Reports',
                'description': 'Create new reports'
            },
            {
                'name': 'reports.export',
                'display_name': 'Export Reports',
                'description': 'Export report data'
            },
            {
                'name': 'reports.schedule',
                'display_name': 'Schedule Reports',
                'description': 'Schedule automated reports'
            },
        ]
    },
    'settings': {
        'display_name': 'Settings',
        'permissions': [
            {
                'name': 'settings.view',
                'display_name': 'View Settings',
                'description': 'View application settings'
            },
            {
                'name': 'settings.update',
                'display_name': 'Update Settings',
                'description': 'Update application settings'
            },
            {
                'name': 'settings.system',
                'display_name': 'System Settings',
                'description': 'Manage system-wide settings'
            },
            {
                'name': 'settings.security',
                'display_name': 'Security Settings',
                'description': 'Manage security settings'
            },
        ]
    },
    'email': {
        'display_name': 'Email Management',
        'permissions': [
            {
                'name': 'email.view.logs',
                'display_name': 'View Email Logs',
                'description': 'View email sending logs'
            },
            {
                'name': 'email.send',
                'display_name': 'Send Emails',
                'description': 'Send emails to users'
            },
            {
                'name': 'email.send.bulk',
                'display_name': 'Send Bulk Emails',
                'description': 'Send bulk/mass emails'
            },
            {
                'name': 'email.manage.templates',
                'display_name': 'Manage Email Templates',
                'description': 'Create and edit email templates'
            },
        ]
    },
}


def seed_permissions():
    """Seed all system permissions"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Seeding system permissions...")
        print("=" * 60)
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for module_name, module_data in SYSTEM_PERMISSIONS.items():
            print(f"\n📦 Module: {module_data['display_name']}")
            print("-" * 60)
            
            for perm_data in module_data['permissions']:
                # Check if permission exists
                existing = rbac_service.get_permission_by_name(perm_data['name'])
                
                if existing:
                    # Update if changed
                    if (existing.display_name != perm_data['display_name'] or 
                        existing.description != perm_data.get('description')):
                        rbac_service.update_permission(
                            existing.id,
                            display_name=perm_data['display_name'],
                            description=perm_data.get('description')
                        )
                        print(f"  ✓ Updated: {perm_data['name']}")
                        updated_count += 1
                    else:
                        print(f"  - Exists: {perm_data['name']}")
                        skipped_count += 1
                else:
                    # Create new permission
                    rbac_service.create_permission(
                        name=perm_data['name'],
                        display_name=perm_data['display_name'],
                        module=module_name,
                        description=perm_data.get('description'),
                        is_active=True
                    )
                    print(f"  ✓ Created: {perm_data['name']}")
                    created_count += 1
        
        print("\n" + "=" * 60)
        print("✅ Permission seeding complete!")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {created_count + updated_count + skipped_count}")
        print("=" * 60)
        
        return created_count, updated_count, skipped_count


if __name__ == '__main__':
    try:
        created, updated, skipped = seed_permissions()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error seeding permissions: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
