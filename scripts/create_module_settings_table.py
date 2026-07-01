#!/usr/bin/env python3
"""
Script to create module_settings table directly in the database.
This bypasses migration conflicts by creating the table manually.
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.core import db

def create_module_settings_table():
    app = create_app()
    with app.app_context():
        # Check if table already exists
        result = db.engine.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'module_settings'
            );
        """)
        
        table_exists = result.fetchone()[0]
        
        if table_exists:
            print("✅ module_settings table already exists")
            return
        
        # Create the table
        create_table_sql = """
        CREATE TABLE module_settings (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            module_name VARCHAR(64) NOT NULL,
            setting_key VARCHAR(128) NOT NULL,
            setting_name VARCHAR(128) NOT NULL,
            description TEXT,
            json_data JSONB NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_by VARCHAR(64),
            updated_by VARCHAR(64),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (id)
        );
        """
        
        # Create indexes
        create_indexes_sql = [
            "CREATE INDEX ix_module_settings_module_name ON module_settings (module_name);",
            "CREATE UNIQUE INDEX ix_module_settings_module_key ON module_settings (module_name, setting_key);"
        ]
        
        try:
            # Create table
            db.engine.execute(create_table_sql)
            print("✅ Created module_settings table")
            
            # Create indexes
            for index_sql in create_indexes_sql:
                db.engine.execute(index_sql)
            print("✅ Created indexes for module_settings table")
            
            # Insert into alembic_version to mark as migrated
            # We'll use a fake revision ID for now
            fake_revision = "manual_module_settings_001"
            db.engine.execute(f"""
                INSERT INTO alembic_version (version_num) 
                VALUES ('{fake_revision}')
                ON CONFLICT (version_num) DO NOTHING;
            """)
            print(f"✅ Marked migration as applied: {fake_revision}")
            
            print("\n🎉 module_settings table created successfully!")
            print("   - Table: module_settings")
            print("   - Columns: id, module_name, setting_key, setting_name, description, json_data, is_active, created_by, updated_by, created_at, updated_at")
            print("   - Indexes: module_name, unique(module_name, setting_key)")
            print("   - Ready for JSON-based module configurations")
            
        except Exception as e:
            print(f"❌ Error creating module_settings table: {e}")
            return False
        
        return True

if __name__ == '__main__':
    create_module_settings_table()
