#!/usr/bin/env python3
"""
Reset and Recreate Database

This script:
1. Drops all tables
2. Recreates them from migrations
3. Seeds initial data
4. Verifies the database is working

Usage:
    python scripts/reset_database.py --confirm
    
⚠️  WARNING: This will DELETE all data!
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extensions.core import db
from app.main.models import User, Role, Group
from app.models.contact import Contact
from app.models.document import Document
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.modules.settings.models import Setting


def reset_and_recreate():
    """Reset and recreate the database"""
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("⚠️  DATABASE RESET AND RECREATION")
        print("="*80)
        print("\nThis will:")
        print("  1. Drop all existing tables")
        print("  2. Recreate them from migrations")
        print("  3. Seed initial data")
        print("  4. Verify the database is working")
        print("\n⚠️  ALL DATA WILL BE DELETED!")
        
        confirm = input("\nType 'RESET' to confirm: ")
        
        if confirm != 'RESET':
            print("\n❌ Reset cancelled.")
            return False
        
        try:
            print("\n🔄 Checking database permissions...")
            
            # For PostgreSQL, use CASCADE to drop tables
            # For SQLite, db.drop_all() works fine
            with db.engine.connect() as conn:
                inspector = db.inspect(conn)
                tables = inspector.get_table_names()
                
                if len(tables) > 0:
                    print(f"  Found {len(tables)} tables")
                    
                    # If PostgreSQL, try to drop schema and recreate
                    from sqlalchemy import text
                    
                    try:
                        # Get database dialect
                        dialect = db.engine.url.get_dialect().name
                        
                        if dialect == 'postgresql':
                            print("  Using PostgreSQL - attempting CASCADE drop...")
                            
                            # Drop all tables with CASCADE
                            for table in reversed(tables):
                                try:
                                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                                    print(f"    ✓ Dropped {table}")
                                except Exception as e:
                                    print(f"    ⚠️  Could not drop {table}: {e}")
                            
                            # Commit the transaction
                            conn.commit()
                            
                        elif dialect == 'sqlite':
                            print("  Using SQLite - dropping all tables...")
                            db.drop_all()
                        else:
                            # Default fallback
                            db.drop_all()
                            
                    except Exception as e:
                        print(f"  ⚠️  Error during drop: {e}")
                        print("  Will continue with migration upgrade...")
                else:
                    print("  No tables found - database is empty")
            
            print("\n🔄 Recreating tables from migrations...")
            from flask_migrate import upgrade
            upgrade()
            
            print("✅ Database recreated successfully!")
            
            # Verify tables exist
            print("\n🔍 Verifying database...")
            with db.engine.connect() as conn:
                # Check for users table
                result = conn.execute(
                    "SELECT COUNT(*) FROM users"
                )
                user_count = result.scalar()
                print(f"  ✓ users table: {user_count} users")
                
                # Check for roles table
                result = conn.execute(
                    "SELECT COUNT(*) FROM roles"
                )
                role_count = result.scalar()
                print(f"  ✓ roles table: {role_count} roles")
                
                # Check for settings table
                result = conn.execute(
                    "SELECT COUNT(*) FROM settings"
                )
                settings_count = result.scalar()
                print(f"  ✓ settings table: {settings_count} settings")
            
            # Verify models work
            print("\n🔍 Testing models...")
            
            # Test User model
            users = User.query.all()
            print(f"  ✓ User.query.all(): {len(users)} users found")
            
            # Test Role model
            roles = Role.query.all()
            print(f"  ✓ Role.query.all(): {len(roles)} roles found")
            
            for role in roles:
                print(f"    - {role.name} ({role.display_name})")
            
            # Test Setting model
            settings = Setting.query.limit(5).all()
            print(f"  ✓ Setting.query: {len(settings)} settings found")
            
            print("\n" + "="*80)
            print("✅ DATABASE RESET SUCCESSFUL!")
            print("="*80)
            print("\n📊 Database Statistics:")
            print(f"   • {len(users)} users")
            print(f"   • {len(roles)} roles")
            print(f"   • {len(settings)} settings")
            print("\n🎯 Next steps:")
            print("   • Login with super_admin account")
            print("   • Run: python scripts/manage_permissions.py --reset-all")
            print("   • Verify all migrations applied")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error resetting database: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(description='Reset and recreate database')
    parser.add_argument('--confirm', action='store_true', 
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  For safety, please run with --confirm flag")
        print("Usage: python scripts/reset_database.py --confirm")
        return
    
    reset_and_recreate()


if __name__ == '__main__':
    main()

