#!/usr/bin/env python3
"""
Manage Role Permissions Script

This script can:
1. Set default permissions for all roles
2. Reset permissions for specific roles
3. Show current permission structure
4. Restore safe defaults if site breaks

Usage:
    python scripts/manage_permissions.py --reset-all
    python scripts/manage_permissions.py --reset-role admin
    python scripts/manage_permissions.py --show
    python scripts/manage_permissions.py --restore-safe
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extensions.core import db
from app.main.models import Role
from app.modules.settings.module_settings_service import ModuleSettingsService


# Default permissions for each role
# GRANULAR PERMISSION STRUCTURE:
# - Horizontal: More actions per module (list, view, create, update, delete, import, export, archive, restore, manage)
# - Vertical: More permission levels (super_admin, admin, manager, lead, user, viewer, guest)

DEFAULT_PERMISSIONS = {
    'super_admin': {
        'users': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'roles': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'groups': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'contacts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'accounts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'documents': {'list': True, 'view': True, 'upload': True, 'download': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': True, 'manage': True},
        'settings': {'view': True, 'update': True, 'delete': True, 'manage': True, 'override': True},
        'email_relay': {'view': True, 'send': True, 'configure': True, 'logs': True, 'manage': True, 'queue': True},
        'email': {'view': True, 'send': True, 'configure': True, 'logs': True, 'manage': True, 'queue': True},
        'analytics': {'view': True, 'export': True, 'manage': True, 'advanced': True},
        'tenants': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'manage': True, 'configure': True},
        'organizations': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'manage': True, 'configure': True},
    },
    'admin': {
        'users': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': False, 'import': True, 'export': True, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': False, 'import': True, 'export': True, 'archive': False, 'restore': False, 'manage': True},
        'contacts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': False, 'manage': True},
        'documents': {'list': True, 'view': True, 'upload': True, 'download': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': False, 'manage': True},
        'settings': {'view': True, 'update': True, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': True},
        'email': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': True},
        'analytics': {'view': True, 'export': True, 'manage': False, 'advanced': False},
        'tenants': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': False, 'manage': True, 'configure': False},
        'organizations': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'manage': True, 'configure': False},
    },
    'manager': {
        'users': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'contacts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': False, 'manage': True},
        'documents': {'list': True, 'view': True, 'upload': True, 'download': True, 'update': True, 'delete': True, 'import': True, 'export': True, 'archive': True, 'restore': False, 'manage': True},
        'settings': {'view': True, 'update': False, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': False},
        'email': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': False},
        'analytics': {'view': True, 'export': True, 'manage': False, 'advanced': False},
        'tenants': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
        'organizations': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': False, 'manage': True, 'configure': False},
    },
    'user': {
        'users': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'contacts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': False, 'export': True, 'archive': False, 'restore': False, 'manage': False},
        'documents': {'list': True, 'view': True, 'upload': True, 'download': True, 'update': True, 'delete': True, 'import': False, 'export': True, 'archive': False, 'restore': False, 'manage': False},
        'settings': {'view': False, 'update': False, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': False, 'send': False, 'configure': False, 'logs': False, 'manage': False, 'queue': False},
        'email': {'view': False, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': False},
        'analytics': {'view': False, 'export': False, 'manage': False, 'advanced': False},
        'tenants': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
        'organizations': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
    },
    'viewer': {
        'users': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'contacts': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': True, 'archive': False, 'restore': False, 'manage': False},
        'documents': {'list': True, 'view': True, 'upload': False, 'download': True, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'settings': {'view': False, 'update': False, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': True, 'send': False, 'configure': False, 'logs': False, 'manage': False, 'queue': False},
        'email': {'view': True, 'send': False, 'configure': False, 'logs': False, 'manage': False, 'queue': False},
        'analytics': {'view': True, 'export': False, 'manage': False, 'advanced': False},
        'tenants': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
        'organizations': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
    },
    'lead': {  # NEW: Team lead level between manager and user
        'users': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'contacts': {'list': True, 'view': True, 'create': True, 'update': True, 'delete': True, 'import': False, 'export': True, 'archive': False, 'restore': False, 'manage': True},
        'documents': {'list': True, 'view': True, 'upload': True, 'download': True, 'update': True, 'delete': False, 'import': False, 'export': True, 'archive': False, 'restore': False, 'manage': False},
        'settings': {'view': True, 'update': False, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': False},
        'email': {'view': True, 'send': True, 'configure': False, 'logs': True, 'manage': False, 'queue': False},
        'analytics': {'view': True, 'export': True, 'manage': False, 'advanced': False},
        'tenants': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
        'organizations': {'list': True, 'view': True, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
    },
    'guest': {  # NEW: Guest/public access level
        'users': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'roles': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'groups': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'contacts': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'documents': {'list': False, 'view': False, 'upload': False, 'download': False, 'update': False, 'delete': False, 'import': False, 'export': False, 'archive': False, 'restore': False, 'manage': False},
        'settings': {'view': False, 'update': False, 'delete': False, 'manage': False, 'override': False},
        'email_relay': {'view': False, 'send': False, 'configure': False, 'logs': False, 'manage': False, 'queue': False},
        'email': {'view': False, 'send': False, 'configure': False, 'logs': False, 'manage': False, 'queue': False},
        'analytics': {'view': False, 'export': False, 'manage': False, 'advanced': False},
        'tenants': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
        'organizations': {'list': False, 'view': False, 'create': False, 'update': False, 'delete': False, 'manage': False, 'configure': False},
    },
}


def create_app():
    """Create Flask application"""
    from app import create_app as app_factory
    return app_factory()


def check_tables_exist(app):
    """Check if required tables exist"""
    with app.app_context():
        try:
            # Try to query the roles table to verify it exists
            role_count = Role.query.count()
            return role_count >= 0  # If we can count, table exists
        except Exception as e:
            print(f"Error checking tables: {e}")
            return False


def show_permissions(app):
    """Show current permissions for all roles"""
    with app.app_context():
        # Check if tables exist
        if not check_tables_exist(app):
            print("\n❌ Error: Database tables do not exist!")
            print("\n📝 Please run migrations first:")
            print("   flask db upgrade")
            print("\n   Or if database is empty:")
            print("   flask db upgrade")
            return
        
        roles = Role.query.all()
        
        print("\n" + "="*80)
        print("CURRENT PERMISSIONS")
        print("="*80)
        
        for role in roles:
            print(f"\n{role.display_name} ({role.name})")
            print("-" * 80)
            
            if role.permissions:
                permissions = role.permissions if isinstance(role.permissions, dict) else {}
                for module, actions in permissions.items():
                    print(f"  {module}:")
                    for action, value in actions.items():
                        status = "✓" if value else "✗"
                        print(f"    {status} {action}")
            else:
                print("  No permissions set")
        
        print("\n" + "="*80)


def set_role_permissions(app, role_name, permissions):
    """Set permissions for a specific role"""
    with app.app_context():
        if not check_tables_exist(app):
            print("\n❌ Error: Database tables do not exist!")
            print("📝 Please run migrations first: flask db upgrade")
            return False
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ Role '{role_name}' not found")
            return False
        
        role.permissions = permissions
        db.session.commit()
        print(f"✅ Updated permissions for {role.display_name} ({role.name})")
        return True


def reset_all_permissions(app):
    """Reset all roles to default permissions"""
    with app.app_context():
        if not check_tables_exist(app):
            print("\n❌ Error: Database tables do not exist!")
            print("📝 Please run migrations first: flask db upgrade")
            return False
        
        roles = Role.query.all()
        updated = 0
        
        print("\nResetting permissions for all roles...")
        
        for role in roles:
            if role.name in DEFAULT_PERMISSIONS:
                role.permissions = DEFAULT_PERMISSIONS[role.name]
                updated += 1
                print(f"  ✓ Reset {role.display_name} ({role.name})")
        
        db.session.commit()
        print(f"\n✅ Reset permissions for {updated} roles")
        return True


def reset_role_permissions(app, role_name):
    """Reset permissions for a specific role"""
    with app.app_context():
        if not check_tables_exist(app):
            print("\n❌ Error: Database tables do not exist!")
            print("📝 Please run migrations first: flask db upgrade")
            return False
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ Role '{role_name}' not found")
            return False
        
        if role.name in DEFAULT_PERMISSIONS:
            role.permissions = DEFAULT_PERMISSIONS[role.name]
            db.session.commit()
            print(f"✅ Reset permissions for {role.display_name} ({role.name})")
            return True
        else:
            print(f"❌ No default permissions defined for role '{role_name}'")
            return False


def restore_safe_permissions(app):
    """Restore safe default permissions when site breaks"""
    print("\n🔧 RESTORING SAFE DEFAULT PERMISSIONS")
    print("This will set all roles to their default permissions...")
    
    try:
        # Set safe defaults for all roles
        for role_name in DEFAULT_PERMISSIONS:
            try:
                set_role_permissions(app, role_name, DEFAULT_PERMISSIONS[role_name])
            except Exception as e:
                print(f"  ⚠️  Could not restore {role_name}: {e}")
        
        print("\n✅ Safe default permissions restored successfully!")
        print("All roles now have their default permission sets.")
        return True
    except Exception as e:
        print(f"\n❌ Error restoring permissions: {e}")
        return False


def sync_permissions_to_module_settings(app):
    """Sync current Role.permissions into module_settings.role_permissions"""
    with app.app_context():
        try:
            if not check_tables_exist(app):
                print("\n❌ Error: Database tables do not exist!")
                print("📝 Please run migrations first: flask db upgrade")
                return False

            roles = Role.query.filter_by(is_active=True).all()
            permissions_payload = {}

            for role in roles:
                role_perms = role.permissions if isinstance(role.permissions, dict) else {}
                # ensure dict structure module -> action -> bool
                normalized: dict = {}
                for module, actions in (role_perms.items() if role_perms else []):
                    if isinstance(actions, dict):
                        normalized[module] = {}
                        for action, enabled in actions.items():
                            normalized[module][str(action)] = bool(enabled)
                permissions_payload[role.name] = normalized

            service = ModuleSettingsService()
            success = service.set_permissions_setting(permissions_data=permissions_payload, updated_by='cli')
            if success:
                print("\n✅ Synced role permissions to module_settings.role_permissions")
                return True
            else:
                print("\n❌ Failed to write to module_settings.role_permissions")
                return False
        except Exception as e:
            print(f"\n❌ Error syncing permissions to module_settings: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Manage role permissions')
    parser.add_argument('--show', action='store_true', help='Show current permissions')
    parser.add_argument('--reset-all', action='store_true', help='Reset all roles to defaults')
    parser.add_argument('--reset-role', type=str, help='Reset specific role to defaults')
    parser.add_argument('--restore-safe', action='store_true', 
                       help='Restore safe default permissions (use when site breaks)')
    parser.add_argument('--sync-module-settings', action='store_true',
                       help='Sync Role.permissions into module_settings.role_permissions')
    
    args = parser.parse_args()
    
    app = create_app()
    
    if args.show:
        show_permissions(app)
    elif args.reset_all:
        reset_all_permissions(app)
    elif args.reset_role:
        reset_role_permissions(app, args.reset_role)
    elif args.restore_safe:
        restore_safe_permissions(app)
    elif args.sync_module_settings:
        sync_permissions_to_module_settings(app)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

