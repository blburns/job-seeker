#!/usr/bin/env python3
"""
User Management Script for Flask Boilerplate
Creates users with different security levels and permissions
"""

import os
import sys
import argparse
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.main.models import User, Role, Group, db
from app.utils.security import hash_password


def create_app_context():
    """Create Flask application context"""
    app = create_app()
    return app


def create_default_roles():
    """Create default roles if they don't exist"""
    roles_data = [
        {
            'name': 'super_admin',
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'permissions': [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'role.create', 'role.read', 'role.update', 'role.delete',
                'group.create', 'group.read', 'group.update', 'group.delete',
                'system.admin', 'system.config', 'system.logs',
                'dashboard.admin', 'dashboard.stats'
            ],
            'priority': 100,
            'is_system_role': True
        },
        {
            'name': 'admin',
            'display_name': 'Administrator',
            'description': 'Administrative access to user management',
            'permissions': [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'role.read', 'group.read',
                'dashboard.admin', 'dashboard.stats'
            ],
            'priority': 80,
            'is_system_role': True
        },
        {
            'name': 'moderator',
            'display_name': 'Moderator',
            'description': 'Limited administrative access',
            'permissions': [
                'user.read', 'user.update',
                'dashboard.stats'
            ],
            'priority': 60,
            'is_system_role': True
        },
        {
            'name': 'user',
            'display_name': 'Regular User',
            'description': 'Standard user access',
            'permissions': [
                'user.read',
                'dashboard.view'
            ],
            'priority': 20,
            'is_system_role': True
        },
        {
            'name': 'guest',
            'display_name': 'Guest User',
            'description': 'Limited guest access',
            'permissions': [
                'dashboard.view'
            ],
            'priority': 10,
            'is_system_role': True
        }
    ]
    
    created_roles = []
    for role_data in roles_data:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(**role_data)
            db.session.add(role)
            created_roles.append(role_data['name'])
        else:
            # Update existing role with new permissions
            role.permissions = role_data['permissions']
            role.description = role_data['description']
            role.priority = role_data['priority']
    
    db.session.commit()
    return created_roles


def create_default_groups():
    """Create default groups if they don't exist"""
    groups_data = [
        {
            'name': 'super_admins',
            'display_name': 'Super Administrators',
            'description': 'Group for super administrators',
            'is_system_group': True
        },
        {
            'name': 'admins',
            'display_name': 'Administrators',
            'description': 'Group for administrators',
            'is_system_group': True
        },
        {
            'name': 'moderators',
            'display_name': 'Moderators',
            'description': 'Group for moderators',
            'is_system_group': True
        },
        {
            'name': 'users',
            'display_name': 'Regular Users',
            'description': 'Group for regular users',
            'is_system_group': True
        }
    ]
    
    created_groups = []
    for group_data in groups_data:
        group = Group.query.filter_by(name=group_data['name']).first()
        if not group:
            group = Group(**group_data)
            db.session.add(group)
            created_groups.append(group_data['name'])
    
    db.session.commit()
    return created_groups


def assign_roles_to_groups():
    """Assign roles to groups"""
    # Super Admins group gets super_admin role
    super_admin_group = Group.query.filter_by(name='super_admins').first()
    super_admin_role = Role.query.filter_by(name='super_admin').first()
    if super_admin_group and super_admin_role and super_admin_role not in super_admin_group.roles:
        super_admin_group.roles.append(super_admin_role)
    
    # Admins group gets admin role
    admin_group = Group.query.filter_by(name='admins').first()
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_group and admin_role and admin_role not in admin_group.roles:
        admin_group.roles.append(admin_role)
    
    # Moderators group gets moderator role
    moderator_group = Group.query.filter_by(name='moderators').first()
    moderator_role = Role.query.filter_by(name='moderator').first()
    if moderator_group and moderator_role and moderator_role not in moderator_group.roles:
        moderator_group.roles.append(moderator_role)
    
    # Users group gets user role
    user_group = Group.query.filter_by(name='users').first()
    user_role = Role.query.filter_by(name='user').first()
    if user_group and user_role and user_role not in user_group.roles:
        user_group.roles.append(user_role)
    
    db.session.commit()


def create_user(username, email, password, firstname=None, lastname=None, 
                role_name='user', group_name=None, is_active=True):
    """Create a new user with specified role and group"""
    
    # Check if user already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        print(f"❌ User with username '{username}' or email '{email}' already exists!")
        return None
    
    # Get role
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        print(f"❌ Role '{role_name}' not found!")
        return None
    
    # Get group if specified
    group = None
    if group_name:
        group = Group.query.filter_by(name=group_name).first()
        if not group:
            print(f"❌ Group '{group_name}' not found!")
            return None
    
    # Create user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        firstname=firstname,
        lastname=lastname,
        is_active=is_active,
        email_verified=True,  # Auto-verify for script-created users
        created_at=datetime.utcnow()
    )
    
    db.session.add(user)
    db.session.flush()  # Get the user ID
    
    # Assign role
    user.roles.append(role)
    
    # Assign group if specified
    if group:
        user.groups.append(group)
    
    db.session.commit()
    
    print(f"✅ User '{username}' created successfully!")
    print(f"   Email: {email}")
    print(f"   Role: {role.display_name}")
    if group:
        print(f"   Group: {group.display_name}")
    print(f"   Active: {is_active}")
    
    return user


def list_users():
    """List all users with their roles and groups"""
    users = User.query.all()
    
    if not users:
        print("No users found.")
        return
    
    print(f"\n{'Username':<20} {'Email':<30} {'Role':<15} {'Group':<15} {'Active':<8}")
    print("-" * 90)
    
    for user in users:
        role_names = [role.display_name for role in user.roles]
        group_names = [group.display_name for group in user.groups]
        
        print(f"{user.username:<20} {user.email:<30} {', '.join(role_names):<15} {', '.join(group_names):<15} {'Yes' if user.is_active else 'No':<8}")


def list_roles():
    """List all available roles"""
    roles = Role.query.order_by(Role.priority.desc()).all()
    
    if not roles:
        print("No roles found.")
        return
    
    print(f"\n{'Name':<15} {'Display Name':<20} {'Priority':<8} {'Permissions':<50}")
    print("-" * 95)
    
    for role in roles:
        permissions = ', '.join(role.permissions or [])[:47] + '...' if len(', '.join(role.permissions or [])) > 47 else ', '.join(role.permissions or [])
        print(f"{role.name:<15} {role.display_name:<20} {role.priority:<8} {permissions:<50}")


def list_groups():
    """List all available groups"""
    groups = Group.query.all()
    
    if not groups:
        print("No groups found.")
        return
    
    print(f"\n{'Name':<15} {'Display Name':<20} {'Roles':<50}")
    print("-" * 87)
    
    for group in groups:
        role_names = [role.display_name for role in group.roles]
        roles_str = ', '.join(role_names)[:47] + '...' if len(', '.join(role_names)) > 47 else ', '.join(role_names)
        print(f"{group.name:<15} {group.display_name:<20} {roles_str:<50}")


def main():
    parser = argparse.ArgumentParser(description='User Management Script')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create user command
    create_parser = subparsers.add_parser('create', help='Create a new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('email', help='Email address')
    create_parser.add_argument('password', help='Password')
    create_parser.add_argument('--firstname', help='First name')
    create_parser.add_argument('--lastname', help='Last name')
    create_parser.add_argument('--role', default='user', 
                              choices=['super_admin', 'admin', 'moderator', 'user', 'guest'],
                              help='User role (default: user)')
    create_parser.add_argument('--group', 
                              choices=['super_admins', 'admins', 'moderators', 'users'],
                              help='User group')
    create_parser.add_argument('--inactive', action='store_true', help='Create inactive user')
    
    # List commands
    subparsers.add_parser('list-users', help='List all users')
    subparsers.add_parser('list-roles', help='List all roles')
    subparsers.add_parser('list-groups', help='List all groups')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup default roles and groups')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create Flask app context
    app = create_app_context()
    
    with app.app_context():
        if args.command == 'setup':
            print("🔧 Setting up default roles and groups...")
            created_roles = create_default_roles()
            created_groups = create_default_groups()
            assign_roles_to_groups()
            
            if created_roles:
                print(f"✅ Created roles: {', '.join(created_roles)}")
            if created_groups:
                print(f"✅ Created groups: {', '.join(created_groups)}")
            print("✅ Setup complete!")
            
        elif args.command == 'create':
            create_user(
                username=args.username,
                email=args.email,
                password=args.password,
                firstname=args.firstname,
                lastname=args.lastname,
                role_name=args.role,
                group_name=args.group,
                is_active=not args.inactive
            )
            
        elif args.command == 'list-users':
            list_users()
            
        elif args.command == 'list-roles':
            list_roles()
            
        elif args.command == 'list-groups':
            list_groups()


if __name__ == '__main__':
    main()
