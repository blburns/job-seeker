#!/usr/bin/env python3
"""
Inspect current database and rebuild migrations logically
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from app.extensions.core import db
from config.app_config import AppConfig
import sqlalchemy

app = Flask(__name__)
app.config.from_object(AppConfig)
db.init_app(app)

with app.app_context():
    # Inspect current database
    inspector = sqlalchemy.inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("Current database tables:")
    print("=" * 60)
    for table in sorted(tables):
        print(f"  {table}")
    print()
    
    # Check if there's a alembic_version table
    if 'alembic_version' in tables:
        print("Alembic version table exists. Checking current version...")
        result = db.session.execute(db.text("SELECT * FROM alembic_version"))
        rows = result.fetchall()
        for row in rows:
            print(f"  Current version: {row}")
        print()
    
    # Get table schemas
    print("Table details:")
    print("=" * 60)
    for table_name in sorted(tables):
        if table_name == 'alembic_version':
            continue
        print(f"\n{table_name}:")
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Get foreign keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print("  Foreign Keys:")
            for fk in fks:
                print(f"    -> {fk['referred_table']}")

print("\nDone inspecting database.")

