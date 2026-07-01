#!/usr/bin/env python3
"""
Script to insert default roles and groups into the database
Run this after database migrations to populate initial data
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.core import db
from app.main.models import Role, Group


def insert_default_roles():
    """Insert default roles into the database"""
    roles_data = [
        {
            'role_uuid': 'super_admin_role_uuid',
            'name': 'super_admin',
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'permissions': ['*'],
            'priority': 1,
            'is_system_role': True,
            'is_active': True
        },
        {
            'role_uuid': 'admin_role_uuid',
            'name': 'admin',
            'display_name': 'Administrator',
            'description': 'Administrative access to most system functions',
            'permissions': ['user_management', 'group_management', 'role_management', 'system_settings', 'user.read'],
            'priority': 2,
            'is_system_role': True,
            'is_active': True
        },
        {
            'role_uuid': 'staff_role_uuid',
            'name': 'staff',
            'display_name': 'Staff Member',
            'description': 'Staff-level access to operational functions',
            'permissions': ['user_view', 'group_view', 'basic_operations'],
            'priority': 3,
            'is_system_role': True,
            'is_active': True
        },
        {
            'role_uuid': 'user_role_uuid',
            'name': 'user',
            'display_name': 'Standard User',
            'description': 'Basic user access with limited permissions',
            'permissions': ['profile_management', 'basic_view'],
            'priority': 4,
            'is_system_role': True,
            'is_active': True
        }
    ]
    
    for role_data in roles_data:
        # Check if role already exists
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"Created role: {role_data['name']}")
        else:
            print(f"Role already exists: {role_data['name']}")
    
    db.session.commit()


def insert_default_groups():
    """Insert default groups into the database"""
    groups_data = [
        {
            'group_uuid': 'super_admin_group_uuid',
            'name': 'super_admins',
            'display_name': 'Super Administrators',
            'description': 'Group for super administrators with full system access',
            'is_active': True,
            'is_system_group': True
        },
        {
            'group_uuid': 'admin_group_uuid',
            'name': 'administrators',
            'display_name': 'Administrators',
            'description': 'Group for administrators with elevated privileges',
            'is_active': True,
            'is_system_group': True
        },
        {
            'group_uuid': 'staff_group_uuid',
            'name': 'staff',
            'display_name': 'Staff Members',
            'description': 'Group for staff members with operational access',
            'is_active': True,
            'is_system_group': True
        },
        {
            'group_uuid': 'users_group_uuid',
            'name': 'users',
            'display_name': 'Standard Users',
            'description': 'Group for standard users with basic access',
            'is_active': True,
            'is_system_group': True
        }
    ]
    
    for group_data in groups_data:
        # Check if group already exists
        existing_group = Group.query.filter_by(name=group_data['name']).first()
        if not existing_group:
            group = Group(**group_data)
            db.session.add(group)
            print(f"Created group: {group_data['name']}")
        else:
            print(f"Group already exists: {group_data['name']}")
    
    db.session.commit()


def main():
    """Main function to insert default data"""
    app = create_app()
    
    with app.app_context():
        print("Inserting default roles and groups...")
        
        try:
            insert_default_roles()
            insert_default_groups()
            print("✅ Default data insertion completed successfully!")
            
            # Display summary
            print("\n📊 Summary:")
            print(f"Roles: {Role.query.count()}")
            print(f"Groups: {Group.query.count()}")
            
        except Exception as e:
            print(f"❌ Error inserting default data: {e}")
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    main()
