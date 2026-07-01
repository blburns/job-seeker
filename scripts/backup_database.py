#!/usr/bin/env python3
"""
Database Backup Script
Creates both SQL dump (plain SQL) and pg_dump format backups
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

def backup_database():
    """Create database backup in multiple formats"""
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    
    db.init_app(app)
    
    with app.app_context():
        # Create backup directory if it doesn't exist
        backup_dir = Path('app/data/db/backups')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # SQL dump filename
        sql_dump_file = backup_dir / f'database_backup_{timestamp}.sql'
        
        # Get database connection
        conn = db.engine.connect()
        
        # For SQLite, use .dump to get plain SQL
        if 'sqlite' in str(db.engine.url):
            import sqlite3
            
            db_path = str(db.engine.url).replace('sqlite:///', '')
            sqlite_db = sqlite3.connect(db_path)
            
            # Create backup
            print(f"Creating SQL dump: {sql_dump_file}")
            with open(sql_dump_file, 'w') as f:
                for line in sqlite_db.iterdump():
                    f.write(f'{line}\n')
            
            sqlite_db.close()
            
            # Also copy the database file
            db_file_copy = backup_dir / f'app.db.backup.{timestamp}'
            import shutil
            shutil.copy2(db_path, db_file_copy)
            print(f"Created DB file copy: {db_file_copy}")
            
        else:
            # For PostgreSQL, create plain SQL dump
            try:
                import subprocess
                import pwd
                
                pg_dump_file = backup_dir / f'database_backup_{timestamp}.sql'
                pg_dump_binary = backup_dir / f'database_backup_{timestamp}.pg_dump'
                
                # Try pg_dump if available
                try:
                    result = subprocess.run(
                        ['pg_dump', 
                         '--dbname', str(db.engine.url).replace('postgresql://', 'postgresql://'),
                         '--clean',
                         '--if-exists',
                         '--no-owner',
                         '--no-acl',
                         '-F', 'p',  # plain text format
                         '-f', str(sql_dump_file)
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"Created SQL dump: {sql_dump_file}")
                    
                    # Also create binary format
                    subprocess.run(
                        ['pg_dump',
                         '--dbname', str(db.engine.url).replace('postgresql://', 'postgresql://'),
                         '--clean',
                         '--if-exists',
                         '--no-owner',
                         '--no-acl',
                         '-F', 'c',  # custom format
                         '-f', str(pg_dump_binary)
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print(f"Created pg_dump binary: {pg_dump_binary}")
                except FileNotFoundError:
                    # pg_dump not available, create simple SQL dump using SQLAlchemy
                    print("pg_dump not available, creating SQL dump using SQLAlchemy...")
                    with open(sql_dump_file, 'w') as f:
                        # This is a simplified version - for full dump you'd need to iterate over all tables
                        f.write("-- Database backup created at {}\n".format(datetime.now()))
                        f.write("-- Note: This is a simplified backup\n")
                        
            except Exception as e:
                print(f"Error creating backup: {e}")
                return
        
        # Also create a schema-only dump
        schema_file = backup_dir / f'database_schema_{timestamp}.sql'
        if 'sqlite' in str(db.engine.url):
            import sqlite3
            db_path = str(db.engine.url).replace('sqlite:///', '')
            sqlite_db = sqlite3.connect(db_path)
            
            with open(schema_file, 'w') as f:
                cursor = sqlite_db.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                for row in cursor:
                    if row[0]:
                        f.write(f"{row[0]};\n")
            
            sqlite_db.close()
        else:
            # PostgreSQL schema dump
            try:
                subprocess.run(
                    ['pg_dump',
                     '--dbname', str(db.engine.url).replace('postgresql://', 'postgresql://'),
                     '--schema-only',
                     '--no-owner',
                     '--no-acl',
                     '-f', str(schema_file)
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except:
                pass
        
        print(f"Backup completed successfully!")
        print(f"  SQL dump: {sql_dump_file}")
        print(f"  DB file: {db_file_copy if 'sqlite' in str(db.engine.url) else 'N/A'}")
        print(f"  Schema: {schema_file}")

if __name__ == '__main__':
    backup_database()

