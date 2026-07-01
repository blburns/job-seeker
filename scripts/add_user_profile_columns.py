#!/usr/bin/env python3
"""
Add extended profile columns to auth.users.
Run once after adding the fields to the User model.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.core import db


def add_profile_columns():
    app = create_app()
    with app.app_context():
        # Columns to add
        columns = [
            ('organization', 'VARCHAR(128)'),
            ('phone', 'VARCHAR(32)'),
            ('address', 'VARCHAR(255)'),
            ('state', 'VARCHAR(64)'),
            ('zip_code', 'VARCHAR(20)'),
            ('country', 'VARCHAR(64)'),
            ('language', 'VARCHAR(10)'),
            ('timezone', 'VARCHAR(64)'),
            ('currency', 'VARCHAR(10)')
        ]
        
        # Try auth.users first, then public.users
        for schema, table in [('auth', 'users'), ('public', 'users')]:
            print(f"Checking {schema}.{table}...")
            
            # Simple check if table exists by selecting 1 row
            try:
                db.session.execute(db.text(f"SELECT 1 FROM {schema}.{table} LIMIT 1"))
                print(f"Found table {schema}.{table}")
            except Exception as e:
                print(f"Table {schema}.{table} not accessible: {e}")
                db.session.rollback()
                continue
            
            for col_name, col_type in columns:
                # PostgreSQL safe add column
                alter_sql = db.text(f"""
                    ALTER TABLE {schema}.{table}
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                """)
                try:
                    db.session.execute(alter_sql)
                    print(f"✅ Ensured {col_name} exists in {schema}.{table}.")
                except Exception as e:
                    # Fallback for older Postgres without IF NOT EXISTS
                    db.session.rollback()
                    try:
                        alter_sql_force = db.text(f"""
                            ALTER TABLE {schema}.{table}
                            ADD COLUMN {col_name} {col_type};
                        """)
                        db.session.execute(alter_sql_force)
                        print(f"✅ Added {col_name} to {schema}.{table}.")
                    except Exception as e2:
                        print(f"⚠️  Could not add {col_name} (might already exist): {e2}")
                        db.session.rollback()
            
            db.session.commit()
            return True
            
        print("❌ Could not update users table.")
        return False


if __name__ == '__main__':
    success = add_profile_columns()
    sys.exit(0 if success else 1)
