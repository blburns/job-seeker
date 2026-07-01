#!/usr/bin/env python3
"""
Default Account Management Script

This script helps manage the default user accounts, roles, and permissions
created by the migration. It provides utilities to:

1. List all default accounts
2. Reset passwords
3. Check account status
4. Manage roles and permissions

Usage:
    python scripts/manage_default_accounts.py [command] [options]

Commands:
    list                    - List all default accounts
    reset-password <user>   - Reset password for a user
    check-status           - Check account status
    help                   - Show this help message
"""

import sys
import os
import argparse
from flask_bcrypt import generate_password_hash, check_password_hash

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.main.models import User, Role, Group
from app.extensions.core import db


def list_accounts():
    """List all default accounts with their details"""
    app = create_app()
    with app.app_context():
        print("🔍 Default User Accounts:")
        print("=" * 50)
        
        users = User.query.all()
        for user in users:
            print(f"\n👤 {user.username}")
            print(f"   Name: {user.display_name or 'N/A'}")
            print(f"   Email: {user.email}")
            print(f"   Admin: {'Yes' if user.is_admin else 'No'}")
            print(f"   SuperAdmin: {'Yes' if user.is_superadmin else 'No'}")
            print(f"   Active: {'Yes' if user.is_active else 'No'}")
            print(f"   Email Verified: {'Yes' if user.email_verified else 'No'}")
            
            # Show roles
            roles = [role.name for role in user.roles]
            print(f"   Roles: {', '.join(roles) if roles else 'None'}")
            
            # Show groups
            groups = [group.name for group in user.groups]
            print(f"   Groups: {', '.join(groups) if groups else 'None'}")
        
        print("\n🔑 Default Login Credentials:")
        print("=" * 50)
        print("SuperAdmin: superadmin / SuperAdmin123!")
        print("Admin: admin / Admin123!")
        print("Demo: demo / Demo123!")
        
        print("\n⚠️  IMPORTANT SECURITY NOTES:")
        print("=" * 50)
        print("1. Change default passwords immediately in production")
        print("2. Disable or delete unused accounts")
        print("3. Enable two-factor authentication if available")
        print("4. Regularly audit user permissions")


def reset_password(username, new_password):
    """Reset password for a user"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return
        
        # Generate new password hash
        password_hash = generate_password_hash(new_password).decode('utf-8')
        
        # Update user
        user.password_hash = password_hash
        db.session.commit()
        
        print(f"✅ Password reset successfully for user '{username}'")


def check_status():
    """Check the status of all accounts and system"""
    app = create_app()
    with app.app_context():
        print("📊 System Status Check:")
        print("=" * 50)
        
        # Count users
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        superadmin_users = User.query.filter_by(is_superadmin=True).count()
        
        print(f"👥 Users: {total_users} total, {active_users} active")
        print(f"🔐 Admins: {admin_users}, SuperAdmins: {superadmin_users}")
        
        # Count roles and groups
        total_roles = Role.query.count()
        system_roles = Role.query.filter_by(is_system_role=True).count()
        total_groups = Group.query.count()
        system_groups = Group.query.filter_by(is_system_group=True).count()
        
        print(f"🎭 Roles: {total_roles} total, {system_roles} system roles")
        print(f"👥 Groups: {total_groups} total, {system_groups} system groups")
        
        # Check for default accounts
        default_users = ['superadmin', 'admin', 'demo']
        print(f"\n🔍 Default Account Status:")
        for username in default_users:
            user = User.query.filter_by(username=username).first()
            if user:
                status = "✅ Active" if user.is_active else "❌ Inactive"
                verified = "✅ Verified" if user.email_verified else "❌ Unverified"
                print(f"   {username}: {status}, Email: {verified}")
            else:
                print(f"   {username}: ❌ Not found")
        
        # Check database connection
        try:
            db.session.execute("SELECT 1")
            print(f"\n🗄️  Database: ✅ Connected")
        except Exception as e:
            print(f"\n🗄️  Database: ❌ Error - {e}")


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(description='Manage default user accounts')
    parser.add_argument('command', nargs='?', default='list',
                       choices=['list', 'reset-password', 'check-status', 'help'],
                       help='Command to execute')
    parser.add_argument('--username', '-u', help='Username for password reset')
    parser.add_argument('--password', '-p', help='New password for reset')
    
    args = parser.parse_args()
    
    if args.command == 'help':
        print(__doc__)
    elif args.command == 'list':
        list_accounts()
    elif args.command == 'reset-password':
        if not args.username or not args.password:
            print("❌ Error: Username and password required for reset")
            print("Usage: python scripts/manage_default_accounts.py reset-password --username <user> --password <new_pass>")
            return
        reset_password(args.username, args.password)
    elif args.command == 'check-status':
        check_status()
    else:
        print("❌ Unknown command. Use 'help' for usage information.")


if __name__ == '__main__':
    main()
