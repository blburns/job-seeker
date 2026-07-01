#!/usr/bin/env python3
"""
Inspect and Modify Permissions Script

This script allows you to:
1. Check permissions for specific users, roles, or groups
2. View which roles/groups a user belongs to
3. Check which users belong to a role or group
4. Grant/revoke specific permissions for users, roles, or groups
5. Show the effective permissions for a user (combining all their roles/groups)
6. Initialize permissions for new modules
7. Add or remove permission actions for modules

Usage:
    # Check user permissions
    python scripts/inspect_permissions.py --user admin --show-permissions
    
    # Check role permissions
    python scripts/inspect_permissions.py --role admin --show-permissions
    
    # Check group permissions
    python scripts/inspect_permissions.py --group system_admins --show-permissions
    
    # Grant a permission to a role
    python scripts/inspect_permissions.py --role admin --grant-permission users.edit
    
    # Revoke a permission from a role
    python scripts/inspect_permissions.py --role admin --revoke-permission users.edit
    
    # Grant a permission to a user directly (on their roles)
    python scripts/inspect_permissions.py --user admin --grant-permission contacts.delete
    
    # List all members of a role
    python scripts/inspect_permissions.py --role admin --list-members
    
    # Show effective permissions for a user (combines all roles/groups)
    python scripts/inspect_permissions.py --user admin --effective
"""
import sys
import argparse
import uuid
from pathlib import Path
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extensions.core import db
from app.main.models import Role, User, Group


def get_user_by_id_or_name(identifier):
    """Get user by UUID or username"""
    try:
        user_uuid = uuid.UUID(identifier)
        return User.query.filter_by(id=user_uuid).first()
    except (ValueError, TypeError):
        return User.query.filter_by(username=identifier).first()


def get_role_by_id_or_name(identifier):
    """Get role by UUID or name"""
    try:
        role_uuid = uuid.UUID(identifier)
        return Role.query.filter_by(id=role_uuid).first()
    except (ValueError, TypeError):
        return Role.query.filter_by(name=identifier).first()


def get_group_by_id_or_name(identifier):
    """Get group by UUID or name"""
    try:
        group_uuid = uuid.UUID(identifier)
        return Group.query.filter_by(id=group_uuid).first()
    except (ValueError, TypeError):
        return Group.query.filter_by(name=identifier).first()


def parse_permission(permission_str):
    """Parse permission string like 'users.edit' into module and action"""
    if '.' not in permission_str:
        raise ValueError(f"Permission must be in format 'module.action', got: {permission_str}")
    return permission_str.split('.', 1)


def show_role_permissions(role_identifier):
    """Show permissions for a specific role"""
    with app.app_context():
        role = get_role_by_id_or_name(role_identifier)
        if not role:
            print(f"❌ Role '{role_identifier}' not found (tried UUID and name)")
            return False
        
        print(f"\n{'='*80}")
        print(f"ROLE: {role.display_name} ({role.name})")
        print(f"{'='*80}")
        print(f"Description: {role.description}")
        print(f"Priority: {role.priority}")
        print(f"Is System Role: {role.is_system_role}")
        print(f"Is Active: {role.is_active}")
        print(f"\nPermissions:")
        
        if role.permissions:
            for module, actions in role.permissions.items():
                print(f"\n  {module}:")
                if isinstance(actions, dict):
                    for action, value in actions.items():
                        status = "✓" if value else "✗"
                        print(f"    {status} {action}")
                else:
                    print(f"    {actions}")
        else:
            print("  No permissions configured")
        
        print(f"\nMembers: {len(role.users)} users, {len(role.groups)} groups")
        
        return True


def show_group_permissions(group_identifier):
    """Show permissions for a specific group"""
    with app.app_context():
        group = get_group_by_id_or_name(group_identifier)
        if not group:
            print(f"❌ Group '{group_identifier}' not found (tried UUID and name)")
            return False
        
        print(f"\n{'='*80}")
        print(f"GROUP: {group.display_name} ({group.name})")
        print(f"{'='*80}")
        print(f"Description: {group.description}")
        print(f"Is System Group: {group.is_system_group}")
        print(f"Is Active: {group.is_active}")
        
        if group.roles:
            print(f"\nAssociated Roles ({len(group.roles)}):")
            for role in group.roles:
                print(f"  - {role.display_name} ({role.name})")
        else:
            print("\n  No roles associated")
        
        print(f"\nMembers: {len(group.users)} users")
        
        # Show effective permissions from all roles
        print(f"\nEffective Permissions (from all roles):")
        effective_perms = {}
        for role in group.roles:
            if role.is_active and role.permissions:
                for module, actions in role.permissions.items():
                    if module not in effective_perms:
                        effective_perms[module] = {}
                    if isinstance(actions, dict):
                        for action, value in actions.items():
                            # OR logic: if any role grants permission, it's granted
                            if action not in effective_perms[module] or not effective_perms[module][action]:
                                effective_perms[module][action] = value
        
        if effective_perms:
            for module, actions in effective_perms.items():
                print(f"\n  {module}:")
                for action, value in actions.items():
                    status = "✓" if value else "✗"
                    print(f"    {status} {action}")
        else:
            print("  No permissions configured")
        
        return True


def show_user_permissions(user_identifier):
    """Show permissions for a specific user"""
    with app.app_context():
        user = get_user_by_id_or_name(user_identifier)
        if not user:
            print(f"❌ User '{user_identifier}' not found (tried UUID and username)")
            return False
        
        print(f"\n{'='*80}")
        print(f"USER: {user.username}")
        print(f"{'='*80}")
        print(f"Display Name: {user.display_name}")
        print(f"Email: {user.email}")
        print(f"Is Admin: {user.is_admin}")
        print(f"Is Super Admin: {user.is_superadmin}")
        print(f"Is Active: {user.is_active}")
        
        # Show direct roles
        if user.roles:
            print(f"\nDirect Roles ({len(user.roles)}):")
            for role in user.roles:
                print(f"  - {role.display_name} ({role.name})")
        else:
            print("\n  No direct roles assigned")
        
        # Show groups
        if user.groups:
            print(f"\nGroups ({len(user.groups)}):")
            for group in user.groups:
                print(f"  - {group.display_name} ({group.name})")
                if group.roles:
                    print(f"    Roles: {', '.join(r.name for r in group.roles)}")
        else:
            print("\n  No groups assigned")
        
        # Calculate effective permissions from all roles and groups
        print(f"\n{'='*80}")
        print("EFFECTIVE PERMISSIONS")
        print(f"{'='*80}")
        effective_perms = {}
        
        # Collect permissions from direct roles
        for role in user.roles:
            if role.is_active and role.permissions:
                for module, actions in role.permissions.items():
                    if module not in effective_perms:
                        effective_perms[module] = {}
                    if isinstance(actions, dict):
                        for action, value in actions.items():
                            if action not in effective_perms[module] or not effective_perms[module][action]:
                                effective_perms[module][action] = value
        
        # Collect permissions from group roles
        for group in user.groups:
            if group.is_active:
                for role in group.roles:
                    if role.is_active and role.permissions:
                        for module, actions in role.permissions.items():
                            if module not in effective_perms:
                                effective_perms[module] = {}
                            if isinstance(actions, dict):
                                for action, value in actions.items():
                                    if action not in effective_perms[module] or not effective_perms[module][action]:
                                        effective_perms[module][action] = value
        
        if effective_perms:
            for module, actions in effective_perms.items():
                print(f"\n  {module}:")
                for action, value in actions.items():
                    status = "✓" if value else "✗"
                    print(f"    {status} {action}")
        else:
            print("  No permissions configured")
        
        return True


def list_role_members(role_identifier):
    """List all users and groups that have this role"""
    with app.app_context():
        role = get_role_by_id_or_name(role_identifier)
        if not role:
            print(f"❌ Role '{role_identifier}' not found (tried UUID and name)")
            return False
        
        print(f"\n{'='*80}")
        print(f"ROLE: {role.display_name} ({role.name})")
        print(f"{'='*80}")
        
        print(f"\nDirect Users ({len(role.users)}):")
        for user in role.users:
            print(f"  - {user.username} ({user.display_name})")
        
        print(f"\nGroups ({len(role.groups)}):")
        for group in role.groups:
            print(f"  - {group.name} ({group.display_name})")
            print(f"    Group Members: {len(group.users)} users")
        
        return True


def grant_permission(entity_type, entity_identifier, permission):
    """Grant a permission to a user, role, or group"""
    with app.app_context():
        module, action = parse_permission(permission)
        
        if entity_type == 'user':
            entity = get_user_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ User '{entity_identifier}' not found (tried UUID and username)")
                return False
            
            if not entity.roles:
                print(f"❌ User '{entity_identifier}' has no roles assigned")
                return False
            
            print(f"\nGranting {permission} to user '{entity_identifier}'")
            updated_roles = []
            
            for role in entity.roles:
                if not role.permissions:
                    role.permissions = {}
                if module not in role.permissions:
                    role.permissions[module] = {}
                
                print(f"  Updating role '{role.name}'")
                role.permissions[module][action] = True
                updated_roles.append(role)
            
            db.session.commit()
            print(f"✅ Updated permissions for user '{entity_identifier}' across {len(updated_roles)} roles")
            
        elif entity_type == 'role':
            entity = get_role_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ Role '{entity_identifier}' not found (tried UUID and name)")
                return False
            
            if not entity.permissions:
                entity.permissions = {}
            if module not in entity.permissions:
                entity.permissions[module] = {}
            
            entity.permissions[module][action] = True
            db.session.commit()
            print(f"✅ Granted {permission} to role '{entity_identifier}'")
            
        elif entity_type == 'group':
            entity = get_group_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ Group '{entity_identifier}' not found (tried UUID and name)")
                return False
            
            if not entity.roles:
                print(f"❌ Group '{entity_identifier}' has no roles assigned")
                return False
            
            print(f"\nGranting {permission} to group '{entity_identifier}'")
            updated_roles = []
            
            for role in entity.roles:
                if not role.permissions:
                    role.permissions = {}
                if module not in role.permissions:
                    role.permissions[module] = {}
                
                print(f"  Updating role '{role.name}'")
                role.permissions[module][action] = True
                updated_roles.append(role)
            
            db.session.commit()
            print(f"✅ Updated permissions for group '{entity_identifier}' across {len(updated_roles)} roles")
        else:
            print(f"❌ Unknown entity type: {entity_type}")
            return False
        
        return True


def revoke_permission(entity_type, entity_identifier, permission):
    """Revoke a permission from a user, role, or group"""
    with app.app_context():
        module, action = parse_permission(permission)
        
        if entity_type == 'user':
            entity = get_user_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ User '{entity_identifier}' not found (tried UUID and username)")
                return False
            
            if not entity.roles:
                print(f"❌ User '{entity_identifier}' has no roles assigned")
                return False
            
            print(f"\nRevoking {permission} from user '{entity_identifier}'")
            updated_roles = []
            
            for role in entity.roles:
                if role.permissions and module in role.permissions:
                    if action in role.permissions[module]:
                        print(f"  Updating role '{role.name}'")
                        role.permissions[module][action] = False
                        updated_roles.append(role)
            
            db.session.commit()
            print(f"✅ Updated permissions for user '{entity_identifier}' across {len(updated_roles)} roles")
            
        elif entity_type == 'role':
            entity = get_role_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ Role '{entity_identifier}' not found (tried UUID and name)")
                return False
            
            if not entity.permissions or module not in entity.permissions:
                print(f"❌ Permission {permission} not found for role '{entity_identifier}'")
                return False
            
            if action in entity.permissions[module]:
                entity.permissions[module][action] = False
                db.session.commit()
                print(f"✅ Revoked {permission} from role '{entity_identifier}'")
            else:
                print(f"❌ Permission {permission} not found for role '{entity_identifier}'")
                return False
            
        elif entity_type == 'group':
            entity = get_group_by_id_or_name(entity_identifier)
            if not entity:
                print(f"❌ Group '{entity_identifier}' not found (tried UUID and name)")
                return False
            
            if not entity.roles:
                print(f"❌ Group '{entity_identifier}' has no roles assigned")
                return False
            
            print(f"\nRevoking {permission} from group '{entity_identifier}'")
            updated_roles = []
            
            for role in entity.roles:
                if role.permissions and module in role.permissions:
                    if action in role.permissions[module]:
                        print(f"  Updating role '{role.name}'")
                        role.permissions[module][action] = False
                        updated_roles.append(role)
            
            db.session.commit()
            print(f"✅ Updated permissions for group '{entity_identifier}' across {len(updated_roles)} roles")
        else:
            print(f"❌ Unknown entity type: {entity_type}")
            return False
        
        return True


def initialize_module_permissions(module_name, actions=None):
    """Initialize permissions structure for a new module"""
    with app.app_context():
        # Default actions if not provided
        if actions is None:
            actions = ['create', 'read', 'update', 'delete', 'manage', 'view']
        
        print(f"\n🔧 Initializing permissions for module: {module_name}")
        print(f"   Actions: {', '.join(actions)}")
        
        roles = Role.query.filter_by(is_active=True).all()
        updated_count = 0
        
        for role in roles:
            if not role.permissions:
                role.permissions = {}
            
            if module_name not in role.permissions:
                role.permissions[module_name] = {}
            
            # Initialize all actions for this role
            for action in actions:
                if action not in role.permissions[module_name]:
                    # Set default based on role priority
                    if role.priority >= 90:  # super_admin, admin
                        role.permissions[module_name][action] = True
                    elif role.priority >= 70:  # manager
                        role.permissions[module_name][action] = action in ['read', 'view', 'create']
                    elif role.priority >= 50:  # user
                        role.permissions[module_name][action] = action in ['read', 'view']
                    else:  # guest, viewer
                        role.permissions[module_name][action] = action == 'view'
                    
                    updated_count += 1
                    print(f"   ✓ {role.name}.{module_name}.{action} = {role.permissions[module_name][action]}")
        
        db.session.commit()
        print(f"\n✅ Initialized {updated_count} permissions for module '{module_name}' across {len(roles)} roles")
        return True


def add_module_action(module_name, action_name):
    """Add a new action to an existing module"""
    with app.app_context():
        print(f"\n➕ Adding action '{action_name}' to module '{module_name}'")
        
        roles = Role.query.filter_by(is_active=True).all()
        updated_count = 0
        
        for role in roles:
            if not role.permissions:
                role.permissions = {}
            
            if module_name not in role.permissions:
                role.permissions[module_name] = {}
            
            if action_name not in role.permissions[module_name]:
                # Set default based on role priority and action type
                restricted_actions = ['delete', 'manage', 'configure']
                if role.priority >= 90:
                    role.permissions[module_name][action_name] = True
                elif role.priority >= 70:
                    role.permissions[module_name][action_name] = action_name not in restricted_actions
                elif role.priority >= 50:
                    role.permissions[module_name][action_name] = action_name in ['read', 'view']
                else:
                    role.permissions[module_name][action_name] = action_name == 'view'
                
                updated_count += 1
        
        db.session.commit()
        print(f"✅ Added action '{action_name}' to module '{module_name}' for {len(roles)} roles")
        return True


def remove_module_action(module_name, action_name):
    """Remove an action from a module"""
    with app.app_context():
        print(f"\n➖ Removing action '{action_name}' from module '{module_name}'")
        
        roles = Role.query.filter_by(is_active=True).all()
        updated_count = 0
        
        for role in roles:
            if role.permissions and module_name in role.permissions:
                if action_name in role.permissions[module_name]:
                    del role.permissions[module_name][action_name]
                    updated_count += 1
        
        db.session.commit()
        print(f"✅ Removed action '{action_name}' from module '{module_name}' for {updated_count} roles")
        return True


def list_all_modules():
    """List all modules that have permission configurations"""
    with app.app_context():
        roles = Role.query.filter_by(is_active=True).all()
        modules = set()
        
        for role in roles:
            if role.permissions:
                modules.update(role.permissions.keys())
        
        if modules:
            print(f"\n📋 Configured Modules ({len(modules)}):")
            for module in sorted(modules):
                print(f"   - {module}")
                
                # Show actions for this module
                for role in roles:
                    if role.permissions and module in role.permissions:
                        actions = list(role.permissions[module].keys())
                        if len(set(actions)) > 1:  # Only show if unique across roles
                            print(f"     Actions: {', '.join(sorted(set(actions)))}")
                            break
        else:
            print("\n   No modules configured")
        
        return list(modules)


def create_app():
    """Create Flask application"""
    from app import create_app as app_factory
    return app_factory()


def main():
    parser = argparse.ArgumentParser(description='Inspect and modify permissions')
    
    # Entity selection
    parser.add_argument('--user', type=str, help='User name to inspect/modify')
    parser.add_argument('--role', type=str, help='Role name to inspect/modify')
    parser.add_argument('--group', type=str, help='Group name to inspect/modify')
    
    # Display actions
    parser.add_argument('--show-permissions', action='store_true', help='Show permissions')
    parser.add_argument('--list-members', action='store_true', help='List members (for roles)')
    parser.add_argument('--effective', action='store_true', help='Show effective permissions (for users)')
    
    # Permission modification
    parser.add_argument('--grant-permission', type=str, help='Grant a permission (format: module.action)')
    parser.add_argument('--revoke-permission', type=str, help='Revoke a permission (format: module.action)')
    
    # Module management
    parser.add_argument('--list-modules', action='store_true', help='List all modules with permissions')
    parser.add_argument('--init-module', type=str, help='Initialize permissions for a new module')
    parser.add_argument('--init-actions', type=str, nargs='*', help='Actions to initialize (with --init-module)')
    parser.add_argument('--add-action', type=str, nargs=2, metavar=('MODULE', 'ACTION'), 
                       help='Add a new action to a module')
    parser.add_argument('--remove-action', type=str, nargs=2, metavar=('MODULE', 'ACTION'), 
                       help='Remove an action from a module')
    
    args = parser.parse_args()
    
    global app
    app = create_app()
    
    # Handle module management commands first (they don't need entity)
    if args.list_modules:
        list_all_modules()
        return
    elif args.init_module:
        initialize_module_permissions(args.init_module, args.init_actions)
        return
    elif args.add_action:
        add_module_action(args.add_action[0], args.add_action[1])
        return
    elif args.remove_action:
        remove_module_action(args.remove_action[0], args.remove_action[1])
        return
    
    # Determine entity type for entity-specific commands
    entity_type = None
    entity_name = None
    
    if args.user:
        entity_type = 'user'
        entity_name = args.user
    elif args.role:
        entity_type = 'role'
        entity_name = args.role
    elif args.group:
        entity_type = 'group'
        entity_name = args.group
    elif not any([args.grant_permission, args.revoke_permission, args.list_members, args.show_permissions, args.effective]):
        # No entity specified and no module management commands
        parser.print_help()
        return
    
    # Execute entity-specific actions
    if args.grant_permission:
        grant_permission(entity_type, entity_name, args.grant_permission)
    elif args.revoke_permission:
        revoke_permission(entity_type, entity_name, args.revoke_permission)
    elif args.list_members and entity_type == 'role':
        list_role_members(entity_name)
    elif args.show_permissions:
        if entity_type == 'user':
            show_user_permissions(entity_name)
        elif entity_type == 'role':
            show_role_permissions(entity_name)
        elif entity_type == 'group':
            show_group_permissions(entity_name)
    elif args.effective and entity_type == 'user':
        show_user_permissions(entity_name)  # effective is the default for users
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

