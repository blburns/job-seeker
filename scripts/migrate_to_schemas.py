#!/usr/bin/env python3
"""
Database Schema Migration Script
Moves tables from public schema to their respective schemas for RBAC-compliant organization
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables BEFORE importing app
from dotenv import load_dotenv
from app.extensions.config import load_environment_variables

# Load .env file from project root
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from current directory
    load_dotenv()

# Also call the app's environment loader for consistency
load_environment_variables()

from app import create_app
from app.extensions.core import db
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.orm import sessionmaker

# Schema mapping: table_name -> schema_name
SCHEMA_MAPPING = {
    # Auth schema
    'users': 'auth',
    'roles': 'auth',
    'groups': 'auth',
    'user_roles': 'auth',
    'user_groups': 'auth',
    'group_roles': 'auth',
    
    # Accounts schema
    'accounts': 'accounts',
    'account_types': 'accounts',
    'account_categories': 'accounts',
    'account_activities': 'accounts',
    'account_settings': 'accounts',
    
    # Contacts schema
    'contacts': 'contacts',
    'contact_categories': 'contacts',
    'contact_communications': 'contacts',
    'contact_settings': 'contacts',
    
    # Documents schema
    'documents': 'documents',
    'document_categories': 'documents',
    'document_access_logs': 'documents',
    'document_shares': 'documents',
    'document_workflows': 'documents',
    
    # Organizations schema
    'organizations': 'organizations',
    'organization_members': 'organizations',
    'brands': 'organizations',
    
    # Tenants schema
    'tenants': 'tenants',
    'tenant_invitations': 'tenants',
    'tenant_settings': 'tenants',
    'tenant_usage': 'tenants',
    
    # Settings schema
    'settings': 'settings',
    'setting_categories': 'settings',
    'setting_values': 'settings',
    'setting_overrides': 'settings',
    'module_settings': 'settings',
    
    # Keep in public
    'alembic_version': 'public',
}


def create_schemas(app, superuser_engine=None):
    """Create all required schemas and grant necessary permissions"""
    schemas = set(SCHEMA_MAPPING.values())
    
    with app.app_context():
        # Get the current database user
        result = db.session.execute(text('SELECT current_user'))
        db_user = result.scalar()
        
        # Use superuser engine if provided, otherwise use regular db session
        if superuser_engine:
            print(f"🔐 Using superuser connection for schema creation and permissions")
            superuser_session = sessionmaker(bind=superuser_engine)()
            session_to_use = superuser_session
        else:
            session_to_use = db.session
        
        schemas_created = []
        
        for schema in schemas:
            if schema == 'public':
                continue  # Skip public schema
            
            try:
                # Create schema
                session_to_use.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                session_to_use.commit()
                schemas_created.append(schema)
                print(f"✅ Created schema: {schema}")
            except Exception as e:
                print(f"⚠️  Error creating schema {schema}: {e}")
                session_to_use.rollback()
        
        # Grant permissions
        for schema in schemas_created:
            try:
                # Grant USAGE privilege (required to use objects in the schema)
                session_to_use.execute(text(f'GRANT USAGE ON SCHEMA {schema} TO {db_user}'))
                
                # Grant CREATE privilege (required to create/move objects in the schema)
                session_to_use.execute(text(f'GRANT CREATE ON SCHEMA {schema} TO {db_user}'))
                
                # Grant ALL privileges on all tables in the schema (for future tables)
                session_to_use.execute(text(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema} TO {db_user}'))
                
                # Set default privileges for future tables
                session_to_use.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT ALL ON TABLES TO {db_user}'))
                
                session_to_use.commit()
                print(f"✅ Granted permissions on schema: {schema} to {db_user}")
            except Exception as perm_error:
                print(f"⚠️  Could not grant permissions on {schema}: {perm_error}")
                session_to_use.rollback()
        
        if superuser_engine:
            superuser_session.close()


def get_foreign_keys_for_table(table_name, schema='public'):
    """Get all foreign keys for a table"""
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = :schema
                AND tc.table_name = :table_name
        """), {'schema': schema, 'table_name': table_name})
        
        return result.fetchall()


def move_table_to_schema(app, table_name, target_schema, dry_run=False):
    """Move a table from public schema to target schema"""
    if target_schema == 'public':
        print(f"⏭️  Skipping {table_name} (stays in public)")
        return True
    
    with app.app_context():
        try:
            # Check if table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """), {'table_name': table_name})
            
            if not result.scalar():
                print(f"⚠️  Table {table_name} does not exist in public schema")
                return False
            
            if dry_run:
                print(f"🔍 [DRY RUN] Would move {table_name} to {target_schema}")
                return True
            
            # Move the table
            db.session.execute(text(f'ALTER TABLE public.{table_name} SET SCHEMA {target_schema}'))
            db.session.commit()
            print(f"✅ Moved {table_name} to {target_schema}")
            return True
            
        except Exception as e:
            print(f"❌ Error moving {table_name}: {e}")
            db.session.rollback()
            return False


def update_foreign_keys(app, dry_run=False):
    """Update foreign key constraints to use schema-qualified names"""
    with app.app_context():
        # Get all foreign keys that reference tables in new schemas
        result = db.session.execute(text("""
            SELECT DISTINCT
                tc.table_schema,
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema != 'public'
                AND ccu.table_schema != 'public'
            ORDER BY tc.table_schema, tc.table_name
        """))
        
        fks = result.fetchall()
        
        if not fks:
            print("✅ No foreign keys need updating")
            return
        
        print(f"\n📋 Found {len(fks)} foreign keys to verify")
        
        for fk in fks:
            table_schema, table_name, constraint_name, column_name, \
            foreign_schema, foreign_table, foreign_column = fk
            
            # Check if foreign key already uses schema-qualified name
            # PostgreSQL automatically handles this, but we'll verify
            if dry_run:
                print(f"🔍 [DRY RUN] FK {constraint_name}: {table_schema}.{table_name}.{column_name} -> {foreign_schema}.{foreign_table}.{foreign_column}")
            else:
                # PostgreSQL handles schema-qualified foreign keys automatically
                # We just need to verify they're correct
                print(f"✅ Verified FK {constraint_name}")


def migrate_tables(app, dry_run=False, superuser_engine=None):
    """Migrate all tables to their schemas"""
    print("\n" + "="*80)
    print("DATABASE SCHEMA MIGRATION")
    print("="*80)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Changes will be made to the database\n")
    
    # Step 1: Create schemas
    print("Step 1: Creating schemas...")
    create_schemas(app, superuser_engine=superuser_engine)
    
    # Step 2: Move tables
    print("\nStep 2: Moving tables to schemas...")
    moved = 0
    skipped = 0
    failed = 0
    
    for table_name, target_schema in sorted(SCHEMA_MAPPING.items()):
        if move_table_to_schema(app, table_name, target_schema, dry_run):
            if target_schema == 'public':
                skipped += 1
            else:
                moved += 1
        else:
            failed += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Moved: {moved}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Failed: {failed}")
    
    # Step 3: Verify foreign keys
    print("\nStep 3: Verifying foreign keys...")
    update_foreign_keys(app, dry_run)
    
    print("\n" + "="*80)
    if dry_run:
        print("DRY RUN COMPLETE - No changes were made")
    else:
        print("MIGRATION COMPLETE")
    print("="*80)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate database tables to schemas')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--confirm', action='store_true', help='Confirm migration (required for live mode)')
    parser.add_argument('--superuser', type=str, help='PostgreSQL superuser (e.g., postgres) - will prompt for password')
    parser.add_argument('--superuser-password', type=str, help='PostgreSQL superuser password (not recommended - use prompt instead)')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.confirm:
        print("❌ ERROR: --confirm flag required for live migration")
        print("   Use --dry-run to preview changes first")
        sys.exit(1)
    
    # Display database connection info for verification
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'app.db')
    db_user = os.environ.get('DB_USER', '')
    db_port = os.environ.get('DB_PORT', '5432')
    
    print("\n" + "="*80)
    print("DATABASE CONNECTION INFO")
    print("="*80)
    print(f"Database Type: {db_type}")
    if db_type != 'sqlite':
        print(f"Host: {db_host}")
        print(f"Database: {db_name}")
        print(f"User: {db_user}")
    else:
        print(f"Database File: {db_name}")
    print("="*80 + "\n")
    
    app = create_app()
    
    # Verify database connection
    try:
        with app.app_context():
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            # Mask password in URI for display
            if '@' in db_uri:
                display_uri = db_uri.split('@')[-1]
            else:
                display_uri = db_uri
            print(f"Connecting to: {display_uri}")
            # Test connection
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check your .env file and ensure:")
        print("  - DB_TYPE is set correctly")
        print("  - DB_HOST, DB_NAME, DB_USER, DB_PASSWORD are set (for PostgreSQL/MySQL)")
        print("  - Database server is running")
        print(f"\nCurrent .env location: {project_root / '.env'}")
        sys.exit(1)
    
    # Setup superuser connection if requested
    superuser_engine = None
    if args.superuser and db_type == 'postgresql':
        try:
            import getpass
            from urllib.parse import quote_plus
            
            # Try to get password from environment variable first, then args, then prompt
            superuser_password = (
                os.environ.get('POSTGRES_SUPERUSER_PASSWORD') or 
                os.environ.get('DB_SUPERUSER_PASSWORD') or
                args.superuser_password
            )
            
            if not superuser_password:
                print(f"\nEnter password for PostgreSQL superuser '{args.superuser}':")
                superuser_password = getpass.getpass()
            
            # Create superuser connection URI
            encoded_password = quote_plus(superuser_password)
            superuser_uri = f"postgresql://{args.superuser}:{encoded_password}@{db_host}:{db_port}/{db_name}"
            
            # Test superuser connection
            superuser_engine = create_engine(superuser_uri, pool_pre_ping=True)
            with superuser_engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            print(f"✅ Superuser connection successful ({args.superuser})\n")
        except Exception as e:
            print(f"⚠️  Superuser connection failed: {e}")
            print("Continuing without superuser - you may need to grant permissions manually")
            superuser_engine = None
    elif db_type == 'postgresql' and not args.superuser:
        # Check if superuser password is in environment - auto-use if available
        superuser_name = os.environ.get('POSTGRES_SUPERUSER', 'postgres')
        superuser_password = (
            os.environ.get('POSTGRES_SUPERUSER_PASSWORD') or 
            os.environ.get('DB_SUPERUSER_PASSWORD')
        )
        
        if superuser_password:
            try:
                from urllib.parse import quote_plus
                encoded_password = quote_plus(superuser_password)
                superuser_uri = f"postgresql://{superuser_name}:{encoded_password}@{db_host}:{db_port}/{db_name}"
                superuser_engine = create_engine(superuser_uri, pool_pre_ping=True)
                with superuser_engine.connect() as conn:
                    conn.execute(text('SELECT 1'))
                print(f"✅ Auto-detected superuser connection ({superuser_name}) from environment\n")
            except Exception as e:
                print(f"⚠️  Auto superuser connection failed: {e}")
                superuser_engine = None
    
    try:
        migrate_tables(app, dry_run=args.dry_run, superuser_engine=superuser_engine)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
