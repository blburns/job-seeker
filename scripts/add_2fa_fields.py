#!/usr/bin/env python3
"""
Add 2FA fields to users table
Run this script to add two-factor authentication fields
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db

def add_2fa_fields():
    """Add 2FA fields to the users table"""
    app = create_app()
    
    with app.app_context():
        # SQL to add 2FA fields
        sql = """
        -- Add 2FA fields to users table
        ALTER TABLE auth.users 
        ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32),
        ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS totp_enabled_at TIMESTAMP,
        ADD COLUMN IF NOT EXISTS backup_codes JSON;
        
        -- Create index for 2FA enabled users
        CREATE INDEX IF NOT EXISTS idx_users_totp_enabled ON auth.users(totp_enabled) WHERE totp_enabled = TRUE;
        """
        
        try:
            # Execute SQL
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ 2FA fields added to users table successfully")
            print("✓ Index created for 2FA enabled users")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error adding 2FA fields: {e}")
            return False

if __name__ == '__main__':
    print("Adding 2FA fields to users table...")
    success = add_2fa_fields()
    sys.exit(0 if success else 1)
