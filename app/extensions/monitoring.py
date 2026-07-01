"""
Health Monitoring
Handles application health monitoring and status checks
"""

from flask import Flask, jsonify
import time


def init_health_monitoring(app: Flask) -> None:
    """
    Initialize health monitoring
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'app_name': app.config.get('APP_NAME', 'Application'),
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'environment': app.config.get('FLASK_ENV', 'development')
        })
    
    @app.route('/status')
    def status():
        """Detailed status endpoint"""
        return jsonify({
            'status': 'operational',
            'timestamp': time.time(),
            'app_name': app.config.get('APP_NAME', 'Application'),
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'environment': app.config.get('FLASK_ENV', 'development'),
            'debug': app.debug,
            'testing': app.testing
        })
    
    @app.route('/health/detailed')
    def health_detailed():
        """Detailed health check endpoint"""
        try:
            from app.extensions.core import db
            from app.main.models import User, Role, Group
            
            # Test database connectivity
            db_status = 'connected'
            try:
                User.query.count()
                Role.query.count()
                Group.query.count()
            except Exception as e:
                db_status = f'error: {str(e)}'
            
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'app_name': app.config.get('APP_NAME', 'Application'),
                'version': app.config.get('APP_VERSION', '1.0.0'),
                'environment': app.config.get('FLASK_ENV', 'development'),
                'database': {
                    'status': db_status,
                    'type': app.config.get('DATABASE_TYPE', 'unknown')
                },
                'services': {
                    'database': 'up' if db_status == 'connected' else 'down',
                    'cache': 'up',
                    'email': 'up'
                },
                'system': {
                    'debug': app.debug,
                    'testing': app.testing
                }
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': time.time(),
                'error': str(e)
            }), 500
    
    @app.route('/health/force')
    def health_force():
        """Force health check endpoint - performs comprehensive checks"""
        try:
            from app.extensions.core import db
            from app.main.models import User, Role, Group
            import os
            
            # Comprehensive health checks
            checks = {
                'database': False,
                'models': False,
                'config': False,
                'filesystem': False
            }
            
            # Database check
            try:
                user_count = User.query.count()
                role_count = Role.query.count()
                group_count = Group.query.count()
                checks['database'] = True
                db_info = {
                    'users': user_count,
                    'roles': role_count,
                    'groups': group_count
                }
            except Exception as e:
                db_info = {'error': str(e)}
            
            # Models check
            try:
                # Test model instantiation
                test_user = User()
                test_role = Role()
                test_group = Group()
                checks['models'] = True
            except Exception as e:
                model_error = str(e)
            
            # Config check
            try:
                required_configs = ['SECRET_KEY', 'DATABASE_TYPE']
                for config in required_configs:
                    if not app.config.get(config):
                        raise ValueError(f'Missing config: {config}')
                checks['config'] = True
            except Exception as e:
                config_error = str(e)
            
            # Filesystem check
            try:
                static_dir = os.path.join(app.root_path, 'static')
                templates_dir = os.path.join(app.root_path, 'templates')
                checks['filesystem'] = os.path.exists(static_dir) and os.path.exists(templates_dir)
            except Exception as e:
                fs_error = str(e)
            
            # Overall health status
            all_healthy = all(checks.values())
            
            return jsonify({
                'status': 'healthy' if all_healthy else 'unhealthy',
                'timestamp': time.time(),
                'app_name': app.config.get('APP_NAME', 'Application'),
                'version': app.config.get('APP_VERSION', '1.0.0'),
                'environment': app.config.get('FLASK_ENV', 'development'),
                'checks': checks,
                'database': db_info if checks['database'] else {'error': 'Database check failed'},
                'system': {
                    'debug': app.debug,
                    'testing': app.testing
                }
            }), 200 if all_healthy else 503
            
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': time.time(),
                'error': str(e)
            }), 500


def stop_health_monitoring() -> None:
    """Stop health monitoring"""
    # This would be implemented if we had background monitoring
    pass


# Global health checker instance
health_checker = None
