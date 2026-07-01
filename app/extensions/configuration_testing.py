"""
Configuration Testing Framework
Provides utilities for testing configuration in different environments
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List
from flask import Flask
from .configuration_validation import validate_configuration


class ConfigurationTester:
    """Test configuration in different environments"""
    
    def __init__(self):
        self.test_configs = {}
        self.temp_dirs = []
    
    def create_test_config(self, environment: str, overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a test configuration for a specific environment
        
        Args:
            environment: Environment name (development, testing, production)
            overrides: Configuration overrides
            
        Returns:
            Test configuration dictionary
        """
        base_config = {
            'SECRET_KEY': 'test-secret-key-for-testing-only',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-for-testing-only',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'WTF_CSRF_ENABLED': False,
            'TESTING': True,
            'FLASK_ENV': environment,
            'FLASK_DEBUG': environment == 'development',
            'MAIL_SUPPRESS_SEND': True,
            'LOG_LEVEL': 'DEBUG'
        }
        
        if environment == 'production':
            base_config.update({
                'FLASK_DEBUG': False,
                'SESSION_COOKIE_SECURE': True,
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Lax',
                'WTF_CSRF_ENABLED': True
            })
        elif environment == 'testing':
            base_config.update({
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                'WTF_CSRF_ENABLED': False,
                'MAIL_SUPPRESS_SEND': True
            })
        
        # Apply overrides
        if overrides:
            base_config.update(overrides)
        
        return base_config
    
    def test_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a configuration by creating a temporary Flask app
        
        Args:
            config: Configuration to test
            
        Returns:
            Test results dictionary
        """
        # Create temporary Flask app
        app = Flask(__name__)
        app.config.update(config)
        
        # Validate configuration
        is_valid, errors, warnings = validate_configuration(app)
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'config_summary': {
                'environment': config.get('FLASK_ENV', 'unknown'),
                'debug_mode': config.get('FLASK_DEBUG', False),
                'database_type': 'sqlite' if 'sqlite' in config.get('SQLALCHEMY_DATABASE_URI', '') else 'other',
                'csrf_enabled': config.get('WTF_CSRF_ENABLED', True),
                'testing_mode': config.get('TESTING', False)
            }
        }
    
    def test_all_environments(self) -> Dict[str, Dict[str, Any]]:
        """
        Test configuration for all supported environments
        
        Returns:
            Dictionary with test results for each environment
        """
        environments = ['development', 'testing', 'production']
        results = {}
        
        for env in environments:
            config = self.create_test_config(env)
            results[env] = self.test_configuration(config)
        
        return results
    
    def test_database_configurations(self) -> Dict[str, Dict[str, Any]]:
        """
        Test different database configurations
        
        Returns:
            Dictionary with test results for each database type
        """
        database_configs = {
            'sqlite': {
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                'DATABASE_TYPE': 'sqlite'
            },
            'postgresql': {
                'SQLALCHEMY_DATABASE_URI': 'postgresql://user:pass@localhost/testdb',
                'DATABASE_TYPE': 'postgresql',
                'DB_HOST': 'localhost',
                'DB_USER': 'user',
                'DB_PASSWORD': 'pass',
                'DB_NAME': 'testdb'
            },
            'mysql': {
                'SQLALCHEMY_DATABASE_URI': 'mysql+pymysql://user:pass@localhost/testdb',
                'DATABASE_TYPE': 'mysql',
                'DB_HOST': 'localhost',
                'DB_USER': 'user',
                'DB_PASSWORD': 'pass',
                'DB_NAME': 'testdb'
            }
        }
        
        results = {}
        for db_type, db_config in database_configs.items():
            config = self.create_test_config('testing', db_config)
            results[db_type] = self.test_configuration(config)
        
        return results
    
    def cleanup(self) -> None:
        """Clean up temporary resources"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        self.temp_dirs.clear()


def run_configuration_tests() -> Dict[str, Any]:
    """
    Run comprehensive configuration tests
    
    Returns:
        Test results summary
    """
    tester = ConfigurationTester()
    
    try:
        # Test all environments
        environment_results = tester.test_all_environments()
        
        # Test database configurations
        database_results = tester.test_database_configurations()
        
        # Calculate overall results
        all_valid = all(
            result['is_valid'] 
            for results in [environment_results, database_results] 
            for result in results.values()
        )
        
        total_tests = len(environment_results) + len(database_results)
        passed_tests = sum(
            1 for results in [environment_results, database_results] 
            for result in results.values() 
            if result['is_valid']
        )
        
        return {
            'overall_success': all_valid,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'environment_results': environment_results,
            'database_results': database_results
        }
    
    finally:
        tester.cleanup()


def init_configuration_testing(app: Flask) -> None:
    """Initialize configuration testing for the application"""
    # Add configuration tester to app context
    app.configuration_tester = ConfigurationTester()
    
    # Add test command if in development
    if app.config.get('FLASK_ENV') == 'development':
        @app.cli.command('test-config')
        def test_configuration_command():
            """Test application configuration"""
            results = run_configuration_tests()
            
            print("Configuration Test Results:")
            print(f"Overall Success: {results['overall_success']}")
            print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
            
            if not results['overall_success']:
                print("\nFailed Tests:")
                for test_type, test_results in results.items():
                    if isinstance(test_results, dict):
                        for test_name, result in test_results.items():
                            if not result['is_valid']:
                                print(f"  {test_type}.{test_name}: {result['errors']}")
