#!/usr/bin/env python3
"""
Create Default Roles and Groups Script

This script creates default roles and groups for the Identity Manager system.
Run this after setting up the database with the new Role and Group models.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.modules.users.models import Role, Group, User

def create_default_roles():
    """Create default system roles"""
    roles = [
        {
            'name': 'superadmin',
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'permissions': [
                'user.manage', 'user.delete', 'user.view_all',
                'role.manage', 'role.delete', 'role.view_all',
                'group.manage', 'group.delete', 'group.view_all',
                'admin.dashboard', 'audit.view_all', 'system.settings',
                'security.manage', 'reports.generate'
            ],
            'priority': 100,
            'is_system_role': True
        },
        {
            'name': 'admin',
            'display_name': 'Administrator',
            'description': 'System administration with most permissions',
            'permissions': [
                'user.manage', 'user.view_all',
                'role.view', 'group.manage', 'group.view_all',
                'admin.dashboard', 'audit.view', 'system.settings',
                'security.view', 'reports.view'
            ],
            'priority': 80,
            'is_system_role': True
        },
        {
            'name': 'manager',
            'display_name': 'Manager',
            'description': 'Team management with limited administrative access',
            'permissions': [
                'user.view_team', 'user.manage_team',
                'group.view_team', 'group.manage_team',
                'reports.view_team', 'audit.view_team'
            ],
            'priority': 60,
            'is_system_role': False
        },
        {
            'name': 'user',
            'display_name': 'Standard User',
            'description': 'Basic user access with personal account management',
            'permissions': [
                'user.view_own', 'user.edit_own',
                'profile.view', 'profile.edit'
            ],
            'priority': 20,
            'is_system_role': True
        },
        {
            'name': 'guest',
            'display_name': 'Guest User',
            'description': 'Limited access for temporary or external users',
            'permissions': [
                'user.view_own'
            ],
            'priority': 10,
            'is_system_role': False
        }
    ]
    
    created_roles = []
    for role_data in roles:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if existing_role:
            print(f"Role '{role_data['name']}' already exists, skipping...")
            created_roles.append(existing_role)
        else:
            role = Role(**role_data)
            db.session.add(role)
            created_roles.append(role)
            print(f"Created role: {role_data['display_name']}")
    
    return created_roles

def create_default_groups():
    """Create default system groups"""
    groups = [
        {
            'name': 'system_admins',
            'display_name': 'System Administrators',
            'description': 'Core system administration team',
            'is_system_group': True
        },
        {
            'name': 'it_support',
            'display_name': 'IT Support',
            'description': 'IT support and help desk team',
            'is_system_group': False
        },
        {
            'name': 'security_team',
            'display_name': 'Security Team',
            'description': 'Security and compliance team',
            'is_system_group': False
        },
        {
            'name': 'developers',
            'display_name': 'Development Team',
            'description': 'Software development team',
            'is_system_group': False
        },
        {
            'name': 'users',
            'display_name': 'General Users',
            'description': 'Standard system users',
            'is_system_group': True
        }
    ]
    
    created_groups = []
    for group_data in groups:
        existing_group = Group.query.filter_by(name=group_data['name']).first()
        if existing_group:
            print(f"Group '{group_data['name']}' already exists, skipping...")
            created_groups.append(existing_group)
        else:
            group = Group(**group_data)
            db.session.add(group)
            created_groups.append(group)
            print(f"Created group: {group_data['display_name']}")
    
    return created_groups

def assign_default_roles_to_users():
    """Assign default roles to existing users based on their current permissions"""
    # Get the default roles
    superadmin_role = Role.query.filter_by(name='superadmin').first()
    admin_role = Role.query.filter_by(name='admin').first()
    user_role = Role.query.filter_by(name='user').first()
    
    if not all([superadmin_role, admin_role, user_role]):
        print("Default roles not found, skipping user role assignment...")
        return
    
    # Assign roles to existing users
    users = User.query.all()
    for user in users:
        if user.roles.count() == 0:  # Only assign if no roles are set
            if user.is_superadmin:
                user.roles.append(superadmin_role)
                print(f"Assigned Super Admin role to {user.username}")
            elif user.is_admin:
                user.roles.append(admin_role)
                print(f"Assigned Admin role to {user.username}")
            else:
                user.roles.append(user_role)
                print(f"Assigned User role to {user.username}")

def assign_default_groups_to_users():
    """Assign default groups to existing users"""
    # Get the default groups
    system_admins_group = Group.query.filter_by(name='system_admins').first()
    users_group = Group.query.filter_by(name='users').first()
    
    if not all([system_admins_group, users_group]):
        print("Default groups not found, skipping group assignment...")
        return
    
    # Assign groups to existing users
    users = User.query.all()
    for user in users:
        if user.groups.count() == 0:  # Only assign if no groups are set
            if user.is_superadmin or user.is_admin:
                user.groups.append(system_admins_group)
                print(f"Added {user.username} to System Administrators group")
            else:
                user.groups.append(users_group)
                print(f"Added {user.username} to General Users group")

def assign_roles_to_groups():
    """Assign default roles to groups"""
    # Get roles and groups
    admin_role = Role.query.filter_by(name='admin').first()
    user_role = Role.query.filter_by(name='user').first()
    manager_role = Role.query.filter_by(name='manager').first()
    
    system_admins_group = Group.query.filter_by(name='system_admins').first()
    users_group = Group.query.filter_by(name='users').first()
    it_support_group = Group.query.filter_by(name='it_support').first()
    security_team_group = Group.query.filter_by(name='security_team').first()
    developers_group = Group.query.filter_by(name='developers').first()
    
    if not all([admin_role, user_role, system_admins_group, users_group]):
        print("Required roles or groups not found, skipping group role assignment...")
        return
    
    # Assign roles to groups
    if system_admins_group and system_admins_group.roles.count() == 0:
        system_admins_group.roles.append(admin_role)
        print("Assigned Admin role to System Administrators group")
    
    if users_group and users_group.roles.count() == 0:
        users_group.roles.append(user_role)
        print("Assigned User role to General Users group")
    
    if it_support_group and it_support_group.roles.count() == 0:
        it_support_group.roles.append(manager_role)
        print("Assigned Manager role to IT Support group")
    
    if security_team_group and security_team_group.roles.count() == 0:
        security_team_group.roles.append(manager_role)
        print("Assigned Manager role to Security Team group")
    
    if developers_group and developers_group.roles.count() == 0:
        developers_group.roles.append(user_role)
        print("Assigned User role to Development Team group")

def main():
    """Main function to create default roles and groups"""
    app = create_app()
    
    with app.app_context():
        print("Creating default roles...")
        roles = create_default_roles()
        
        print("\nCreating default groups...")
        groups = create_default_groups()
        
        print("\nAssigning default roles to existing users...")
        assign_default_roles_to_users()

        print("\nAssigning default groups to existing users...")
        assign_default_groups_to_users()

        print("\nAssigning default roles to groups...")
        assign_roles_to_groups()
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Default roles and groups created successfully!")
        print(f"Created {len(roles)} roles and {len(groups)} groups")
        
        # Print summary
        print("\n📋 Summary:")
        print("Roles created:")
        for role in roles:
            print(f"  - {role.display_name} ({role.name})")
        
        print("\nGroups created:")
        for group in groups:
            print(f"  - {group.display_name} ({group.name})")

if __name__ == '__main__':
    main() 