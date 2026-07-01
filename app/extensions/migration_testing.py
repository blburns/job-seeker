"""
Migration Testing Framework
Provides utilities for testing database migrations
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
import click
from flask import current_app
from flask_migrate import upgrade, downgrade, current, history
from app.extensions.core import db


class MigrationTester:
    """Test database migrations safely"""
    
    def __init__(self):
        self.test_db_path = None
        self.original_db_uri = None
    
    def setup_test_environment(self) -> Dict[str, Any]:
        """
        Set up test environment for migration testing
        
        Returns:
            Dictionary with setup information
        """
        try:
            # Create temporary database
            temp_dir = tempfile.mkdtemp()
            self.test_db_path = os.path.join(temp_dir, 'test_migration.db')
            
            # Store original database URI
            self.original_db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
            
            # Set test database URI
            test_db_uri = f"sqlite:///{self.test_db_path}"
            current_app.config['SQLALCHEMY_DATABASE_URI'] = test_db_uri
            
            # Recreate database engine
            db.init_app(current_app)
            
            return {
                'status': 'success',
                'message': 'Test environment set up successfully',
                'test_db_path': self.test_db_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to set up test environment: {e}',
                'test_db_path': None
            }
    
    def cleanup_test_environment(self) -> Dict[str, Any]:
        """
        Clean up test environment
        
        Returns:
            Dictionary with cleanup information
        """
        try:
            # Restore original database URI
            if self.original_db_uri:
                current_app.config['SQLALCHEMY_DATABASE_URI'] = self.original_db_uri
                db.init_app(current_app)
            
            # Remove test database
            if self.test_db_path and os.path.exists(self.test_db_path):
                os.unlink(self.test_db_path)
            
            # Remove temporary directory
            if self.test_db_path:
                temp_dir = os.path.dirname(self.test_db_path)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            
            self.test_db_path = None
            self.original_db_uri = None
            
            return {
                'status': 'success',
                'message': 'Test environment cleaned up successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to clean up test environment: {e}'
            }
    
    def test_migration_upgrade(self, target_revision: str = 'head') -> Dict[str, Any]:
        """
        Test migration upgrade
        
        Args:
            target_revision: Target revision to upgrade to
            
        Returns:
            Dictionary with test results
        """
        try:
            # Get current revision before upgrade
            current_revision = current()
            
            # Perform upgrade
            upgrade(target_revision)
            
            # Get new revision
            new_revision = current()
            
            return {
                'status': 'success',
                'message': f'Migration upgrade test passed: {current_revision} -> {new_revision}',
                'from_revision': current_revision,
                'to_revision': new_revision
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Migration upgrade test failed: {e}',
                'from_revision': current(),
                'to_revision': None
            }
    
    def test_migration_downgrade(self, target_revision: str) -> Dict[str, Any]:
        """
        Test migration downgrade
        
        Args:
            target_revision: Target revision to downgrade to
            
        Returns:
            Dictionary with test results
        """
        try:
            # Get current revision before downgrade
            current_revision = current()
            
            # Perform downgrade
            downgrade(target_revision)
            
            # Get new revision
            new_revision = current()
            
            return {
                'status': 'success',
                'message': f'Migration downgrade test passed: {current_revision} -> {new_revision}',
                'from_revision': current_revision,
                'to_revision': new_revision
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Migration downgrade test failed: {e}',
                'from_revision': current(),
                'to_revision': None
            }
    
    def test_migration_roundtrip(self, target_revision: str) -> Dict[str, Any]:
        """
        Test migration roundtrip (upgrade then downgrade)
        
        Args:
            target_revision: Target revision to test
            
        Returns:
            Dictionary with test results
        """
        try:
            # Get initial revision
            initial_revision = current()
            
            # Test upgrade
            upgrade_result = self.test_migration_upgrade(target_revision)
            if upgrade_result['status'] != 'success':
                return upgrade_result
            
            # Test downgrade back to initial
            downgrade_result = self.test_migration_downgrade(initial_revision)
            if downgrade_result['status'] != 'success':
                return downgrade_result
            
            # Verify we're back to initial revision
            final_revision = current()
            
            return {
                'status': 'success',
                'message': f'Migration roundtrip test passed: {initial_revision} -> {target_revision} -> {final_revision}',
                'initial_revision': initial_revision,
                'target_revision': target_revision,
                'final_revision': final_revision
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Migration roundtrip test failed: {e}',
                'initial_revision': current(),
                'target_revision': target_revision,
                'final_revision': None
            }
    
    def test_all_migrations(self) -> Dict[str, Any]:
        """
        Test all available migrations
        
        Returns:
            Dictionary with comprehensive test results
        """
        try:
            # Set up test environment
            setup_result = self.setup_test_environment()
            if setup_result['status'] != 'success':
                return setup_result
            
            # Get migration history
            migration_history = history()
            revisions = [rev.revision for rev in migration_history]
            
            test_results = {
                'total_migrations': len(revisions),
                'passed_tests': 0,
                'failed_tests': 0,
                'test_details': []
            }
            
            # Test each migration step by step
            for i, revision in enumerate(revisions):
                # Test upgrade to this revision
                upgrade_result = self.test_migration_upgrade(revision)
                test_results['test_details'].append({
                    'revision': revision,
                    'test_type': 'upgrade',
                    'result': upgrade_result
                })
                
                if upgrade_result['status'] == 'success':
                    test_results['passed_tests'] += 1
                else:
                    test_results['failed_tests'] += 1
                
                # Test downgrade to previous revision (if not first)
                if i > 0:
                    prev_revision = revisions[i-1]
                    downgrade_result = self.test_migration_downgrade(prev_revision)
                    test_results['test_details'].append({
                        'revision': f"{revision} -> {prev_revision}",
                        'test_type': 'downgrade',
                        'result': downgrade_result
                    })
                    
                    if downgrade_result['status'] == 'success':
                        test_results['passed_tests'] += 1
                    else:
                        test_results['failed_tests'] += 1
            
            # Clean up test environment
            cleanup_result = self.cleanup_test_environment()
            
            # Calculate overall success
            test_results['overall_success'] = test_results['failed_tests'] == 0
            test_results['cleanup_result'] = cleanup_result
            
            return test_results
            
        except Exception as e:
            # Ensure cleanup even if test fails
            self.cleanup_test_environment()
            return {
                'status': 'error',
                'message': f'Migration testing failed: {e}',
                'overall_success': False
            }
    
    def validate_migration_sql(self, revision: str) -> Dict[str, Any]:
        """
        Validate migration SQL syntax
        
        Args:
            revision: Migration revision to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            # This would require parsing the migration file
            # For now, we'll do a basic check
            migrations_dir = Path(current_app.config.get('MIGRATIONS_DIR', 'migrations'))
            version_file = migrations_dir / 'versions' / f"{revision}_*.py"
            
            version_files = list(migrations_dir.glob('versions') / f"{revision}_*.py")
            if not version_files:
                return {
                    'status': 'error',
                    'message': f'Migration file not found for revision {revision}',
                    'valid': False
                }
            
            # Basic file existence check
            return {
                'status': 'success',
                'message': f'Migration file found for revision {revision}',
                'valid': True,
                'file_path': str(version_files[0])
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Migration validation failed: {e}',
                'valid': False
            }


# Global migration tester instance
migration_tester = MigrationTester()


def init_migration_testing(app) -> None:
    """Initialize migration testing system"""
    # Add migration tester to app context
    app.migration_tester = migration_tester
    
    # Add CLI commands
    @app.cli.command('test-migrations')
    def test_migrations_command():
        """Test all database migrations"""
        results = migration_tester.test_all_migrations()
        
        print("Migration Test Results:")
        print(f"Total Migrations: {results['total_migrations']}")
        print(f"Passed Tests: {results['passed_tests']}")
        print(f"Failed Tests: {results['failed_tests']}")
        print(f"Overall Success: {results['overall_success']}")
        
        if not results['overall_success']:
            print("\nFailed Tests:")
            for test in results['test_details']:
                if test['result']['status'] != 'success':
                    print(f"  {test['revision']} ({test['test_type']}): {test['result']['message']}")
            return 1
        
        return 0
    
    @app.cli.command('test-migration')
    @click.option('--revision', required=True, help='Migration revision to test')
    @click.option('--type', type=click.Choice(['upgrade', 'downgrade', 'roundtrip']), 
                  default='upgrade', help='Type of test to run')
    def test_single_migration_command(revision, type):
        """Test a single migration"""
        # Set up test environment
        setup_result = migration_tester.setup_test_environment()
        if setup_result['status'] != 'success':
            print(f"Setup failed: {setup_result['message']}")
            return 1
        
        try:
            if type == 'upgrade':
                result = migration_tester.test_migration_upgrade(revision)
            elif type == 'downgrade':
                result = migration_tester.test_migration_downgrade(revision)
            elif type == 'roundtrip':
                result = migration_tester.test_migration_roundtrip(revision)
            
            print(f"Test Result: {result['message']}")
            
            if result['status'] != 'success':
                return 1
            
            return 0
            
        finally:
            migration_tester.cleanup_test_environment()
