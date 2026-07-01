"""
Database Backup and Recovery System
Handles database backup and recovery operations
"""

import os
import subprocess
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import click
from app.extensions.core import db


class DatabaseBackupManager:
    """Manages database backup and recovery operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(os.getcwd()) / 'app' / 'data' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> Dict[str, Any]:
        """
        Create a database backup
        
        Args:
            backup_name: Custom name for the backup (optional)
            
        Returns:
            Dictionary with backup information
        """
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if not backup_name:
                backup_name = f"backup_{timestamp}"
            
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            # Get database configuration
            db_url = db.engine.url
            
            if db_url.drivername == 'sqlite':
                return self._backup_sqlite(db_url, backup_file)
            elif db_url.drivername == 'postgresql':
                return self._backup_postgresql(db_url, backup_file)
            elif db_url.drivername in ['mysql', 'mariadb']:
                return self._backup_mysql(db_url, backup_file)
            else:
                return {
                    'status': 'error',
                    'message': f'Backup not supported for database type: {db_url.drivername}',
                    'backup_file': None
                }
                
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'backup_file': None
            }
    
    def _backup_sqlite(self, db_url, backup_file: Path) -> Dict[str, Any]:
        """Create SQLite backup"""
        try:
            # SQLite backup is just copying the database file
            db_path = db_url.database
            if not os.path.exists(db_path):
                return {
                    'status': 'error',
                    'message': f'Database file not found: {db_path}',
                    'backup_file': None
                }
            
            shutil.copy2(db_path, backup_file)
            
            return {
                'status': 'success',
                'message': 'SQLite backup created successfully',
                'backup_file': str(backup_file),
                'backup_size': backup_file.stat().st_size
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'SQLite backup failed: {e}',
                'backup_file': None
            }
    
    def _backup_postgresql(self, db_url, backup_file: Path) -> Dict[str, Any]:
        """Create PostgreSQL backup using pg_dump"""
        try:
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '--host', db_url.host or 'localhost',
                '--port', str(db_url.port or 5432),
                '--username', db_url.username or 'postgres',
                '--dbname', db_url.database,
                '--file', str(backup_file),
                '--verbose',
                '--no-password'
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            if db_url.password:
                env['PGPASSWORD'] = db_url.password
            
            # Run pg_dump
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'pg_dump failed: {result.stderr}',
                    'backup_file': None
                }
            
            return {
                'status': 'success',
                'message': 'PostgreSQL backup created successfully',
                'backup_file': str(backup_file),
                'backup_size': backup_file.stat().st_size
            }
            
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'pg_dump not found. Please install PostgreSQL client tools.',
                'backup_file': None
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'PostgreSQL backup failed: {e}',
                'backup_file': None
            }
    
    def _backup_mysql(self, db_url, backup_file: Path) -> Dict[str, Any]:
        """Create MySQL/MariaDB backup using mysqldump"""
        try:
            # Build mysqldump command
            cmd = [
                'mysqldump',
                '--host', db_url.host or 'localhost',
                '--port', str(db_url.port or 3306),
                '--user', db_url.username or 'root',
                '--password=' + (db_url.password or ''),
                '--single-transaction',
                '--routines',
                '--triggers',
                db_url.database
            ]
            
            # Run mysqldump and redirect output to file
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'mysqldump failed: {result.stderr}',
                    'backup_file': None
                }
            
            return {
                'status': 'success',
                'message': 'MySQL backup created successfully',
                'backup_file': str(backup_file),
                'backup_size': backup_file.stat().st_size
            }
            
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'mysqldump not found. Please install MySQL client tools.',
                'backup_file': None
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'MySQL backup failed: {e}',
                'backup_file': None
            }
    
    def restore_backup(self, backup_file: str) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Dictionary with restore information
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return {
                    'status': 'error',
                    'message': f'Backup file not found: {backup_file}',
                    'restored': False
                }
            
            # Get database configuration
            db_url = db.engine.url
            
            if db_url.drivername == 'sqlite':
                return self._restore_sqlite(db_url, backup_path)
            elif db_url.drivername == 'postgresql':
                return self._restore_postgresql(db_url, backup_path)
            elif db_url.drivername in ['mysql', 'mariadb']:
                return self._restore_mysql(db_url, backup_path)
            else:
                return {
                    'status': 'error',
                    'message': f'Restore not supported for database type: {db_url.drivername}',
                    'restored': False
                }
                
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'restored': False
            }
    
    def _restore_sqlite(self, db_url, backup_path: Path) -> Dict[str, Any]:
        """Restore SQLite backup"""
        try:
            db_path = db_url.database
            shutil.copy2(backup_path, db_path)
            
            return {
                'status': 'success',
                'message': 'SQLite backup restored successfully',
                'restored': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'SQLite restore failed: {e}',
                'restored': False
            }
    
    def _restore_postgresql(self, db_url, backup_path: Path) -> Dict[str, Any]:
        """Restore PostgreSQL backup using psql"""
        try:
            # Build psql command
            cmd = [
                'psql',
                '--host', db_url.host or 'localhost',
                '--port', str(db_url.port or 5432),
                '--username', db_url.username or 'postgres',
                '--dbname', db_url.database,
                '--file', str(backup_path),
                '--quiet'
            ]
            
            # Set password via environment variable
            env = os.environ.copy()
            if db_url.password:
                env['PGPASSWORD'] = db_url.password
            
            # Run psql
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'psql restore failed: {result.stderr}',
                    'restored': False
                }
            
            return {
                'status': 'success',
                'message': 'PostgreSQL backup restored successfully',
                'restored': True
            }
            
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'psql not found. Please install PostgreSQL client tools.',
                'restored': False
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'PostgreSQL restore failed: {e}',
                'restored': False
            }
    
    def _restore_mysql(self, db_url, backup_path: Path) -> Dict[str, Any]:
        """Restore MySQL/MariaDB backup using mysql"""
        try:
            # Build mysql command
            cmd = [
                'mysql',
                '--host', db_url.host or 'localhost',
                '--port', str(db_url.port or 3306),
                '--user', db_url.username or 'root',
                '--password=' + (db_url.password or ''),
                db_url.database
            ]
            
            # Run mysql with backup file as input
            with open(backup_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return {
                    'status': 'error',
                    'message': f'mysql restore failed: {result.stderr}',
                    'restored': False
                }
            
            return {
                'status': 'success',
                'message': 'MySQL backup restored successfully',
                'restored': True
            }
            
        except FileNotFoundError:
            return {
                'status': 'error',
                'message': 'mysql not found. Please install MySQL client tools.',
                'restored': False
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'MySQL restore failed: {e}',
                'restored': False
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_file in self.backup_dir.glob('*.sql'):
            stat = backup_file.stat()
            backups.append({
                'name': backup_file.stem,
                'file': str(backup_file),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old backup files
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Dictionary with cleanup information
        """
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            removed_count = 0
            removed_size = 0
            
            for backup_file in self.backup_dir.glob('*.sql'):
                if backup_file.stat().st_mtime < cutoff_time:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    removed_count += 1
                    removed_size += file_size
            
            return {
                'status': 'success',
                'message': f'Cleaned up {removed_count} old backup files',
                'removed_count': removed_count,
                'removed_size': removed_size
            }
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'removed_count': 0,
                'removed_size': 0
            }


# Global backup manager instance
db_backup_manager = DatabaseBackupManager()


def init_database_backup(app) -> None:
    """Initialize database backup system"""
    # Add backup manager to app context
    app.db_backup_manager = db_backup_manager
    
    # Add CLI commands
    @app.cli.command('db-backup')
    @click.option('--name', help='Custom backup name')
    def database_backup_command(name):
        """Create database backup"""
        result = db_backup_manager.create_backup(name)
        
        if result['status'] == 'success':
            print(f"Backup created: {result['backup_file']}")
            print(f"Size: {result['backup_size']} bytes")
        else:
            print(f"Backup failed: {result['message']}")
            return 1
        
        return 0
    
    @app.cli.command('db-restore')
    @click.option('--file', required=True, help='Backup file to restore')
    def database_restore_command(file):
        """Restore database from backup"""
        result = db_backup_manager.restore_backup(file)
        
        if result['status'] == 'success':
            print("Database restored successfully")
        else:
            print(f"Restore failed: {result['message']}")
            return 1
        
        return 0
    
    @app.cli.command('db-list-backups')
    def database_list_backups_command():
        """List available backups"""
        backups = db_backup_manager.list_backups()
        
        if not backups:
            print("No backups found")
            return
        
        print("Available Backups:")
        for backup in backups:
            print(f"  {backup['name']} - {backup['size']} bytes - {backup['created']}")
    
    @app.cli.command('db-cleanup-backups')
    @click.option('--days', default=30, help='Days to keep backups')
    def database_cleanup_backups_command(days):
        """Clean up old backup files"""
        result = db_backup_manager.cleanup_old_backups(days)
        
        if result['status'] == 'success':
            print(f"Cleanup completed: {result['message']}")
            print(f"Removed {result['removed_count']} files ({result['removed_size']} bytes)")
        else:
            print(f"Cleanup failed: {result['message']}")
            return 1
        
        return 0
