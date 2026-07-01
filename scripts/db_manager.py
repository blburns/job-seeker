#!/usr/bin/env python3
"""
Database Management Utility
Provides commands for database operations across different database types
"""

import os
import sys
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.database_config import DatabaseConfig


def create_database():
    """Create database if it doesn't exist (for PostgreSQL, MySQL, etc.)"""
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    
    if db_type == 'sqlite':
        print("SQLite database will be created automatically")
        return True
    
    try:
        # For other database types, we need to create the database first
        db_name = os.environ.get('DB_NAME')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT')
        db_user = os.environ.get('DB_USER')
        db_password = os.environ.get('DB_PASSWORD')
        
        if db_type == 'postgresql':
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            cursor.close()
            conn.close()
            print(f"PostgreSQL database '{db_name}' created successfully")
            
        elif db_type in ['mysql', 'mariadb']:
            import pymysql
            
            conn = pymysql.connect(
                host=db_host,
                port=int(db_port) if db_port else 3306,
                user=db_user,
                password=db_password
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.close()
            conn.close()
            print(f"MySQL/MariaDB database '{db_name}' created successfully")
            
        elif db_type == 'mssql':
            import pyodbc
            
            # MS SQL Server connection string
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_host},{db_port};UID={db_user};PWD={db_password}"
            conn = pyodbc.connect(conn_str, autocommit=True)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            cursor.close()
            conn.close()
            print(f"MS SQL Server database '{db_name}' created successfully")
            
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False


def test_connection():
    """Test database connection"""
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_info = app.config['DATABASE_INFO']
        
        print(f"Testing connection to {db_info['name']} ({db_info['type']})")
        print(f"URI: {db_uri}")
        
        if DatabaseConfig.validate_database_connection(db_uri):
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed!")
            return False


def show_config():
    """Show current database configuration"""
    app = create_app()
    
    with app.app_context():
        db_info = app.config['DATABASE_INFO']
        
        print("Current Database Configuration:")
        print("=" * 40)
        print(f"Type: {db_info['type']}")
        print(f"Name: {db_info['name']}")
        print(f"Host: {db_info['host']}")
        print(f"Port: {db_info['port']}")
        print(f"Database: {db_info['database']}")
        print(f"User: {db_info['user']}")
        print(f"Pool Size: {db_info['pool_size']}")
        print(f"Max Overflow: {db_info['max_overflow']}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Database Management Utility')
    parser.add_argument('command', choices=['create', 'test', 'config'], 
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        success = create_database()
        sys.exit(0 if success else 1)
    elif args.command == 'test':
        success = test_connection()
        sys.exit(0 if success else 1)
    elif args.command == 'config':
        show_config()
        sys.exit(0)


if __name__ == '__main__':
    main()
