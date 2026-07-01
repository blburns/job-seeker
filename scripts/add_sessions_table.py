#!/usr/bin/env python3
"""
Add user_sessions table to database
Run this script to create the sessions table for session management
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db

def add_sessions_table():
    """Add user_sessions table to the database"""
    app = create_app()
    
    with app.app_context():
        # First, enable uuid-ossp extension
        try:
            db.session.execute(db.text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            db.session.commit()
            print("✓ uuid-ossp extension enabled")
        except Exception as e:
            db.session.rollback()
            print(f"⚠ Warning: Could not enable uuid-ossp extension: {e}")
            print("  Attempting to create table without extension...")
        
        # SQL to create sessions table
        # Try with uuid_generate_v4() first, fallback to gen_random_uuid() if needed
        sql = """
        CREATE TABLE IF NOT EXISTS auth.user_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            device_info JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            last_activity TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            remember_me BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            revoked_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON auth.user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON auth.user_sessions(session_token);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON auth.user_sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON auth.user_sessions(is_active);
        """
        
        try:
            # Execute SQL
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ user_sessions table created successfully")
            print("✓ Indexes created successfully")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating sessions table: {e}")
            
            # Try alternative approach with uuid_generate_v4()
            print("  Trying with uuid_generate_v4()...")
            sql_alt = sql.replace("gen_random_uuid()", "uuid_generate_v4()")
            try:
                db.session.execute(db.text(sql_alt))
                db.session.commit()
                print("✓ user_sessions table created successfully (with uuid_generate_v4)")
                print("✓ Indexes created successfully")
                return True
            except Exception as e2:
                db.session.rollback()
                print(f"✗ Error with alternative approach: {e2}")
                return False

if __name__ == '__main__':
    print("Creating user_sessions table...")
    success = add_sessions_table()
    sys.exit(0 if success else 1)
