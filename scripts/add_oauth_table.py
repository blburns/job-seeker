#!/usr/bin/env python3
"""
Add OAuth accounts table
Run this script to create the oauth_accounts table for OAuth integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db

def add_oauth_table():
    """Create the oauth_accounts table"""
    app = create_app()
    
    with app.app_context():
        # SQL to create oauth_accounts table
        sql = """
        -- Create oauth_accounts table
        CREATE TABLE IF NOT EXISTS auth.oauth_accounts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            provider VARCHAR(50) NOT NULL,
            provider_user_id VARCHAR(255) NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TIMESTAMP,
            provider_email VARCHAR(255),
            provider_name VARCHAR(255),
            provider_picture VARCHAR(500),
            provider_data JSONB,
            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW(),
            last_used_at TIMESTAMP,
            CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id)
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_oauth_user_id ON auth.oauth_accounts(user_id);
        CREATE INDEX IF NOT EXISTS idx_oauth_provider ON auth.oauth_accounts(provider);
        CREATE INDEX IF NOT EXISTS idx_oauth_provider_user_id ON auth.oauth_accounts(provider, provider_user_id);
        """
        
        try:
            # Execute SQL
            db.session.execute(db.text(sql))
            db.session.commit()
            print("✓ OAuth accounts table created successfully")
            print("✓ Indexes created for OAuth accounts")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating OAuth accounts table: {e}")
            return False

if __name__ == '__main__':
    print("Creating OAuth accounts table...")
    success = add_oauth_table()
    sys.exit(0 if success else 1)
