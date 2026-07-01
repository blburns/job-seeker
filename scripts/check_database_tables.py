#!/usr/bin/env python3
"""Check what tables exist in the database"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from app.extensions.core import db
from config.app_config import AppConfig
from app.extensions.core import db
import sqlalchemy

app = Flask(__name__)
app.config.from_object(AppConfig)
db.init_app(app)

with app.app_context():
    # Get database URL
    print(f"Database URL: {db.engine.url}")
    
    # Test connection
    try:
        with db.engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Get all tables
            inspector = sqlalchemy.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\nFound {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  - {table}")
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

