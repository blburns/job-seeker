"""
Health API Namespace
Handles health check and system status endpoints
"""

from flask_restx import Namespace, Resource, fields
from flask import jsonify
from datetime import datetime
from app.api.middleware import require_auth

health_ns = Namespace('health', description='Health check and system status operations')

# Response models
health_model = health_ns.model('Health', {
    'status': fields.String(description='Overall system status'),
    'timestamp': fields.DateTime(description='Check timestamp'),
    'version': fields.String(description='Application version'),
    'environment': fields.String(description='Environment name'),
    'services': fields.Raw(description='Service status details')
})

@health_ns.route('/')
class HealthCheck(Resource):
    def get(self):
        """Basic health check endpoint"""
        from version import get_version
        import os
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': get_version(),
            'environment': os.getenv('FLASK_ENV', 'development')
        }

@health_ns.route('/detailed')
class DetailedHealthCheck(Resource):
    @require_auth
    def get(self):
        """Detailed health check with service status"""
        from version import get_version
        import os
        
        # Check database health (simplified for now)
        try:
            from app.extensions.core import db
            db.session.execute('SELECT 1')
            db_health = {'status': True, 'message': 'Database connection healthy'}
        except Exception as e:
            db_health = {'status': False, 'message': str(e)}
        
        # Check cache health (simplified for now)
        try:
            from app.extensions.cache import cache
            cache.set('health_check', 'ok', timeout=1)
            cache_health = {'status': True, 'message': 'Cache connection healthy'}
        except Exception as e:
            cache_health = {'status': False, 'message': str(e)}
        
        # Determine overall status
        overall_status = 'healthy'
        if not db_health['status'] or not cache_health['status']:
            overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': get_version(),
            'environment': os.getenv('FLASK_ENV', 'development'),
            'services': {
                'database': db_health,
                'cache': cache_health
            }
        }

@health_ns.route('/ready')
class ReadinessCheck(Resource):
    def get(self):
        """Readiness check for load balancers"""
        return {'status': 'ready'}, 200

@health_ns.route('/live')
class LivenessCheck(Resource):
    def get(self):
        """Liveness check for container orchestration"""
        return {'status': 'alive'}, 200
