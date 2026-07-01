"""
Database Health Monitoring
Monitors database connection health and provides diagnostics
"""

import time
import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.extensions.core import db


class DatabaseHealthMonitor:
    """Monitors database health and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.health_checks = []
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Check database connection health
        
        Returns:
            Dictionary with connection status and metrics
        """
        start_time = time.time()
        
        try:
            # Test basic connection
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                if test_value != 1:
                    raise SQLAlchemyError("Connection test failed")
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'timestamp': time.time(),
                'error': None
            }
            
        except SQLAlchemyError as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Database connection check failed: {e}")
            
            return {
                'status': 'unhealthy',
                'response_time_ms': round(response_time, 2),
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def check_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics
        
        Returns:
            Dictionary with database information
        """
        try:
            with db.engine.connect() as connection:
                # Get database version
                version_query = text("SELECT version()")
                version_result = connection.execute(version_query)
                version = version_result.scalar()
                
                # Get database size (if supported)
                size_query = text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """)
                
                try:
                    size_result = connection.execute(size_query)
                    db_size = size_result.scalar()
                except SQLAlchemyError:
                    db_size = "Unknown"
                
                # Get connection count
                conn_query = text("""
                    SELECT count(*) as connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                
                try:
                    conn_result = connection.execute(conn_query)
                    active_connections = conn_result.scalar()
                except SQLAlchemyError:
                    active_connections = "Unknown"
                
                return {
                    'version': version,
                    'size': db_size,
                    'active_connections': active_connections,
                    'database_name': db.engine.url.database,
                    'host': db.engine.url.host,
                    'port': db.engine.url.port
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database info check failed: {e}")
            return {
                'version': 'Unknown',
                'size': 'Unknown',
                'active_connections': 'Unknown',
                'database_name': 'Unknown',
                'host': 'Unknown',
                'port': 'Unknown',
                'error': str(e)
            }
    
    def check_table_health(self) -> Dict[str, Any]:
        """
        Check health of application tables
        
        Returns:
            Dictionary with table health information
        """
        try:
            with db.engine.connect() as connection:
                # Get table information
                tables_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY tablename
                """)
                
                try:
                    tables_result = connection.execute(tables_query)
                    tables = []
                    
                    for row in tables_result:
                        tables.append({
                            'schema': row.schemaname,
                            'table': row.tablename,
                            'inserts': row.inserts,
                            'updates': row.updates,
                            'deletes': row.deletes,
                            'live_tuples': row.live_tuples,
                            'dead_tuples': row.dead_tuples
                        })
                    
                    return {
                        'status': 'healthy',
                        'tables': tables,
                        'table_count': len(tables)
                    }
                    
                except SQLAlchemyError:
                    # Fallback for non-PostgreSQL databases
                    return {
                        'status': 'healthy',
                        'tables': [],
                        'table_count': 0,
                        'note': 'Table statistics not available for this database type'
                    }
                
        except SQLAlchemyError as e:
            self.logger.error(f"Table health check failed: {e}")
            return {
                'status': 'unhealthy',
                'tables': [],
                'table_count': 0,
                'error': str(e)
            }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive database health summary
        
        Returns:
            Dictionary with complete health information
        """
        connection_health = self.check_connection()
        db_info = self.check_database_info()
        table_health = self.check_table_health()
        
        overall_status = 'healthy'
        if connection_health['status'] != 'healthy' or table_health['status'] != 'healthy':
            overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'connection': connection_health,
            'database_info': db_info,
            'tables': table_health,
            'timestamp': time.time()
        }
    
    def log_health_check(self) -> None:
        """Log current health status"""
        health_summary = self.get_health_summary()
        
        if health_summary['overall_status'] == 'healthy':
            self.logger.info(f"Database health check passed - Response time: {health_summary['connection']['response_time_ms']}ms")
        else:
            self.logger.warning(f"Database health check failed - {health_summary['connection'].get('error', 'Unknown error')}")


# Global health monitor instance
db_health_monitor = DatabaseHealthMonitor()


def init_database_health_monitoring(app) -> None:
    """Initialize database health monitoring"""
    # Add health monitor to app context
    app.db_health_monitor = db_health_monitor
    
    # Add health check endpoint
    @app.route('/health/database')
    def database_health_endpoint():
        """Database health check endpoint"""
        from flask import jsonify
        health_summary = db_health_monitor.get_health_summary()
        return jsonify(health_summary)
    
    # Add CLI command for health check
    @app.cli.command('db-health')
    def database_health_command():
        """Check database health"""
        health_summary = db_health_monitor.get_health_summary()
        
        print("Database Health Check:")
        print(f"Overall Status: {health_summary['overall_status']}")
        print(f"Connection Status: {health_summary['connection']['status']}")
        print(f"Response Time: {health_summary['connection']['response_time_ms']}ms")
        
        if health_summary['connection']['error']:
            print(f"Error: {health_summary['connection']['error']}")
        
        if health_summary['overall_status'] != 'healthy':
            return 1
        
        return 0
