#!/usr/bin/env python3
"""
Add avatar_path column to auth.users for profile photo uploads.
Run once after adding the avatar_path field to the User model.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.core import db


def add_avatar_column():
    app = create_app()
    with app.app_context():
        # Try auth.users first (schema-based setup), then public.users
        for schema, table in [('auth', 'users'), ('public', 'users')]:
            check_sql = db.text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table AND column_name = 'avatar_path';
            """)
            try:
                result = db.session.execute(check_sql, {'schema': schema, 'table': table})
                if result.fetchone():
                    print(f"✅ {schema}.users.avatar_path column already exists.")
                    return True
                alter_sql = db.text(f"""
                    ALTER TABLE {schema}.{table}
                    ADD COLUMN avatar_path VARCHAR(255) NULL;
                """)
                db.session.execute(alter_sql)
                db.session.commit()
                print(f"✅ Added avatar_path column to {schema}.users.")
                return True
            except Exception as e:
                db.session.rollback()
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    print(f"✅ {schema}.users.avatar_path column already exists.")
                    return True
                # Table might not exist in this schema, try next
                continue
        print("❌ Could not add avatar_path column (auth.users and public.users not found or error).")
        return False


if __name__ == '__main__':
    success = add_avatar_column()
    sys.exit(0 if success else 1)
