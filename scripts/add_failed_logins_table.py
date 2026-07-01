#!/usr/bin/env python3
"""
Add failed_logins table to database
Run this script to create the failed_logins table for security monitoring
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db

def add_failed_logins_table():
    """Add failed_logins table to the database"""
    app = create_app()
    
    with app.app_context():
        # SQL to create failed_logins table
        # Try with uuid_generate_v4() first, fallback to gen_random_uuid() if needed
        sql = """
        CREATE TABLE IF NOT EXISTS auth.failed_logins (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username_or_email VARCHAR(120) NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            attempted_at TIMESTAMP DEFAULT NOW(),
            reason VARCHAR(64)
        );
        
        CREATE INDEX IF NOT EXISTS idx_failed_logins_username ON auth.failed_logins(username_or_email);
        CREATE INDEX IF NOT EXISTS idx_failed_logins_ip ON auth.failed_logins(ip_address);
        CREATE INDEX IF NOT EXISTS idx_failed_logins_attempted_at ON auth.failed_logins(attempted_at);
        """
        
        try:
            # Execute SQL
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ failed_logins table created successfully")
            print("✓ Indexes created successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating failed_logins table: {e}")
            
            # Try alternative approach with uuid_generate_v4()
            print("  Trying with uuid_generate_v4()...")
            sql_alt = sql.replace("gen_random_uuid()", "uuid_generate_v4()")
            try:
                db.session.execute(db.text(sql_alt))
                db.session.commit()
                print("✓ failed_logins table created successfully (with uuid_generate_v4)")
                print("✓ Indexes created successfully")
                return True
            except Exception as e2:
                db.session.rollback()
                print(f"✗ Error with alternative approach: {e2}")
                return False

if __name__ == '__main__':
    print("Creating failed_logins table...")
    success = add_failed_logins_table()
    sys.exit(0 if success else 1)
