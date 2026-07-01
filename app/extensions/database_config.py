"""
Database Configuration Management
Supports multiple database types: SQLite, PostgreSQL, MySQL/MariaDB, MS SQL Server
"""

import os
from typing import Optional, Dict, Any
from urllib.parse import quote_plus


class DatabaseConfig:
    """Database configuration manager for multiple database types"""
    
    SUPPORTED_DATABASES = {
        'sqlite': 'SQLite',
        'postgresql': 'PostgreSQL', 
        'mysql': 'MySQL',
        'mariadb': 'MariaDB',
        'mssql': 'MS SQL Server'
    }
    
    @staticmethod
    def get_database_uri(
        db_type: str = None,
        db_name: str = None,
        db_user: str = None,
        db_password: str = None,
        db_host: str = None,
        db_port: str = None,
        db_options: Dict[str, str] = None
    ) -> str:
        """
        Generate database URI based on database type and parameters
        
        Args:
            db_type: Database type (sqlite, postgresql, mysql, mariadb, mssql)
            db_name: Database name
            db_user: Database username
            db_password: Database password
            db_host: Database host
            db_port: Database port
            db_options: Additional database options
            
        Returns:
            Database URI string
        """
        # Get values from environment if not provided
        db_type = db_type or os.environ.get('DB_TYPE', 'sqlite')
        db_name = db_name or os.environ.get('DB_NAME', 'app.db')
        db_user = db_user or os.environ.get('DB_USER', '')
        db_password = db_password or os.environ.get('DB_PASSWORD', '')
        db_host = db_host or os.environ.get('DB_HOST', '')
        db_port = db_port or os.environ.get('DB_PORT', '')
        db_options = db_options or {}
        
        # Validate database type
        if db_type not in DatabaseConfig.SUPPORTED_DATABASES:
            raise ValueError(f"Unsupported database type: {db_type}. "
                           f"Supported types: {list(DatabaseConfig.SUPPORTED_DATABASES.keys())}")
        
        if db_type == 'sqlite':
            return DatabaseConfig._get_sqlite_uri(db_name)
        elif db_type == 'postgresql':
            return DatabaseConfig._get_postgresql_uri(db_user, db_password, db_host, db_port, db_name, db_options)
        elif db_type in ['mysql', 'mariadb']:
            return DatabaseConfig._get_mysql_uri(db_user, db_password, db_host, db_port, db_name, db_options)
        elif db_type == 'mssql':
            return DatabaseConfig._get_mssql_uri(db_user, db_password, db_host, db_port, db_name, db_options)
        else:
            raise ValueError(f"Database type {db_type} not implemented")
    
    @staticmethod
    def _get_sqlite_uri(db_name: str) -> str:
        """Generate SQLite URI"""
        # Use absolute path for SQLite
        if not os.path.isabs(db_name):
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.getcwd(), 'app', 'data', 'db')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, db_name)
        else:
            db_path = db_name
        
        return f"sqlite:///{db_path}"
    
    @staticmethod
    def _get_postgresql_uri(
        db_user: str, 
        db_password: str, 
        db_host: str, 
        db_port: str, 
        db_name: str,
        db_options: Dict[str, str]
    ) -> str:
        """Generate PostgreSQL URI"""
        if not all([db_user, db_password, db_host, db_name]):
            raise ValueError("PostgreSQL requires user, password, host, and database name")
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(db_password)
        
        # Build options string
        options_str = ""
        if db_options:
            options_list = [f"{k}={v}" for k, v in db_options.items()]
            options_str = "?" + "&".join(options_list)
        
        port_str = f":{db_port}" if db_port else ""
        return f"postgresql://{db_user}:{encoded_password}@{db_host}{port_str}/{db_name}{options_str}"
    
    @staticmethod
    def _get_mysql_uri(
        db_user: str, 
        db_password: str, 
        db_host: str, 
        db_port: str, 
        db_name: str,
        db_options: Dict[str, str]
    ) -> str:
        """Generate MySQL/MariaDB URI"""
        if not all([db_user, db_password, db_host, db_name]):
            raise ValueError("MySQL/MariaDB requires user, password, host, and database name")
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(db_password)
        
        # Default MySQL options
        default_options = {
            'charset': 'utf8mb4',
            'autocommit': 'true',
            'use_unicode': 'true'
        }
        default_options.update(db_options)
        
        # Build options string
        options_list = [f"{k}={v}" for k, v in default_options.items()]
        options_str = "?" + "&".join(options_list)
        
        port_str = f":{db_port}" if db_port else ""
        return f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}{port_str}/{db_name}{options_str}"
    
    @staticmethod
    def _get_mssql_uri(
        db_user: str, 
        db_password: str, 
        db_host: str, 
        db_port: str, 
        db_name: str,
        db_options: Dict[str, str]
    ) -> str:
        """Generate MS SQL Server URI"""
        if not all([db_user, db_password, db_host, db_name]):
            raise ValueError("MS SQL Server requires user, password, host, and database name")
        
        # URL encode password to handle special characters
        encoded_password = quote_plus(db_password)
        
        # Default MS SQL options
        default_options = {
            'driver': 'ODBC Driver 17 for SQL Server',
            'TrustServerCertificate': 'yes'
        }
        default_options.update(db_options)
        
        # Build options string
        options_list = [f"{k}={v}" for k, v in default_options.items()]
        options_str = "?" + "&".join(options_list)
        
        port_str = f":{db_port}" if db_port else ""
        return f"mssql+pyodbc://{db_user}:{encoded_password}@{db_host}{port_str}/{db_name}{options_str}"
    
    @staticmethod
    def get_engine_options(db_type: str) -> Dict[str, Any]:
        """
        Get SQLAlchemy engine options for specific database type
        
        Args:
            db_type: Database type
            
        Returns:
            Dictionary of engine options
        """
        base_options = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'echo': os.environ.get('SQLALCHEMY_ECHO', 'False') == 'True'
        }
        
        if db_type == 'sqlite':
            return {
                **base_options,
                'poolclass': None,  # SQLite doesn't support connection pooling
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 20
                }
            }
        elif db_type == 'postgresql':
            return {
                **base_options,
                'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
                'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
                'connect_args': {
                    'application_name': os.environ.get('APP_NAME', 'Flask App')
                }
            }
        elif db_type in ['mysql', 'mariadb']:
            return {
                **base_options,
                'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
                'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
                'connect_args': {
                    'charset': 'utf8mb4',
                    'autocommit': True
                }
            }
        elif db_type == 'mssql':
            return {
                **base_options,
                'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
                'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
                'connect_args': {
                    'timeout': 30,
                    'autocommit': True
                }
            }
        else:
            return base_options
    
    @staticmethod
    def validate_database_connection(db_uri: str) -> bool:
        """
        Validate database connection
        
        Args:
            db_uri: Database URI
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_uri, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection validation failed: {e}")
            return False
    
    @staticmethod
    def get_database_info() -> Dict[str, Any]:
        """
        Get current database configuration information
        
        Returns:
            Dictionary with database configuration info
        """
        db_type = os.environ.get('DB_TYPE', 'sqlite')
        return {
            'type': db_type,
            'name': DatabaseConfig.SUPPORTED_DATABASES.get(db_type, 'Unknown'),
            'host': os.environ.get('DB_HOST', 'localhost'),
            'port': os.environ.get('DB_PORT', ''),
            'database': os.environ.get('DB_NAME', 'app.db'),
            'user': os.environ.get('DB_USER', ''),
            'pool_size': os.environ.get('DB_POOL_SIZE', '10'),
            'max_overflow': os.environ.get('DB_MAX_OVERFLOW', '20')
        }
