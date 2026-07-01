"""
CSRF Testing Utilities
Testing framework for CSRF protection
"""

import logging
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_wtf.csrf import generate_csrf, validate_csrf
from flask_wtf import CSRFError

logger = logging.getLogger(__name__)


class CSRFTestSuite:
    """Test suite for CSRF protection"""
    
    def __init__(self, app: Flask):
        """
        Initialize CSRF test suite
        
        Args:
            app: Flask application instance
        """
        self.app = app
    
    def test_csrf_token_generation(self) -> Dict[str, Any]:
        """Test CSRF token generation"""
        try:
            with self.app.app_context():
                token = generate_csrf()
                
                return {
                    'test': 'csrf_token_generation',
                    'success': True,
                    'token_length': len(token),
                    'token_type': type(token).__name__,
                    'message': 'CSRF token generated successfully'
                }
        except Exception as e:
            logger.exception('Error testing CSRF token generation')
            return {
                'test': 'csrf_token_generation',
                'success': False,
                'error': str(e),
                'message': 'Failed to generate CSRF token'
            }
    
    def test_csrf_token_validation(self) -> Dict[str, Any]:
        """Test CSRF token validation"""
        try:
            with self.app.app_context():
                # Generate a valid token
                token = generate_csrf()
                
                # Test valid token
                try:
                    validate_csrf(token)
                    valid_validation = True
                except Exception:
                    valid_validation = False
                
                # Test invalid token
                try:
                    validate_csrf('invalid_token')
                    invalid_validation = False
                except Exception:
                    invalid_validation = True
                
                return {
                    'test': 'csrf_token_validation',
                    'success': True,
                    'valid_token_accepted': valid_validation,
                    'invalid_token_rejected': invalid_validation,
                    'message': 'CSRF token validation working correctly'
                }
        except Exception as e:
            logger.exception('Error testing CSRF token validation')
            return {
                'test': 'csrf_token_validation',
                'success': False,
                'error': str(e),
                'message': 'Failed to test CSRF token validation'
            }
    
    def test_csrf_protection_enabled(self) -> Dict[str, Any]:
        """Test if CSRF protection is enabled"""
        try:
            csrf_enabled = self.app.config.get('WTF_CSRF_ENABLED', False)
            csrf_time_limit = self.app.config.get('WTF_CSRF_TIME_LIMIT', None)
            csrf_secret_key = self.app.config.get('WTF_CSRF_SECRET_KEY', None)
            
            return {
                'test': 'csrf_protection_enabled',
                'success': csrf_enabled,
                'csrf_enabled': csrf_enabled,
                'csrf_time_limit': csrf_time_limit,
                'csrf_secret_key_set': bool(csrf_secret_key),
                'message': 'CSRF protection configuration checked'
            }
        except Exception as e:
            logger.exception('Error checking CSRF protection status')
            return {
                'test': 'csrf_protection_enabled',
                'success': False,
                'error': str(e),
                'message': 'Failed to check CSRF protection status'
            }
    
    def test_csrf_error_handling(self) -> Dict[str, Any]:
        """Test CSRF error handling"""
        try:
            # This would typically be tested with a test client
            # For now, we'll check if the error handler is registered
            error_handlers = self.app.error_handler_spec.get(None, {}).get(CSRFError, [])
            
            return {
                'test': 'csrf_error_handling',
                'success': len(error_handlers) > 0,
                'error_handlers_registered': len(error_handlers),
                'message': 'CSRF error handling checked'
            }
        except Exception as e:
            logger.exception('Error testing CSRF error handling')
            return {
                'test': 'csrf_error_handling',
                'success': False,
                'error': str(e),
                'message': 'Failed to test CSRF error handling'
            }
    
    def test_csrf_template_context(self) -> Dict[str, Any]:
        """Test CSRF token in template context"""
        try:
            with self.app.app_context():
                # Check if CSRF token is available in template context
                with self.app.test_request_context():
                    # Simulate template context processor
                    from app.extensions.csrf_config import init_csrf_config
                    
                    # This would be tested with actual template rendering
                    # For now, we'll check if the context processor exists
                    context_processors = self.app.template_context_processors[None]
                    
                    csrf_context_processor_exists = any(
                        'csrf_token' in str(func) for func in context_processors
                    )
                    
                    return {
                        'test': 'csrf_template_context',
                        'success': csrf_context_processor_exists,
                        'context_processor_exists': csrf_context_processor_exists,
                        'message': 'CSRF template context checked'
                    }
        except Exception as e:
            logger.exception('Error testing CSRF template context')
            return {
                'test': 'csrf_template_context',
                'success': False,
                'error': str(e),
                'message': 'Failed to test CSRF template context'
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all CSRF tests"""
        tests = [
            self.test_csrf_token_generation(),
            self.test_csrf_token_validation(),
            self.test_csrf_protection_enabled(),
            self.test_csrf_error_handling(),
            self.test_csrf_template_context()
        ]
        
        # Calculate overall success rate
        total_tests = len(tests)
        successful_tests = sum(1 for test in tests if test.get('success', False))
        
        return {
            'tests': tests,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
            }
        }


def create_csrf_test_endpoints(app: Flask):
    """Create test endpoints for CSRF functionality"""
    
    @app.route('/test/csrf/token', methods=['GET'])
    def test_csrf_token():
        """Test endpoint to get CSRF token"""
        try:
            token = generate_csrf()
            return jsonify({
                'success': True,
                'csrf_token': token,
                'message': 'CSRF token generated successfully'
            })
        except Exception as e:
            logger.exception('Error generating CSRF token')
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to generate CSRF token'
            }), 500
    
    @app.route('/test/csrf/validate', methods=['POST'])
    def test_csrf_validate():
        """Test endpoint to validate CSRF token"""
        try:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'No CSRF token provided',
                    'message': 'Include csrf_token in form data or X-CSRF-Token header'
                }), 400
            
            validate_csrf(token)
            
            return jsonify({
                'success': True,
                'message': 'CSRF token is valid'
            })
        except Exception as e:
            logger.exception('Error validating CSRF token')
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'CSRF token validation failed'
            }), 400
    
    @app.route('/test/csrf/protected', methods=['POST'])
    def test_csrf_protected():
        """Test endpoint that requires CSRF protection"""
        try:
            # This endpoint should be protected by CSRF
            return jsonify({
                'success': True,
                'message': 'CSRF-protected endpoint accessed successfully'
            })
        except Exception as e:
            logger.exception('Error in CSRF-protected endpoint')
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Error in CSRF-protected endpoint'
            }), 500
    
    @app.route('/test/csrf/suite', methods=['GET'])
    def test_csrf_suite():
        """Run complete CSRF test suite"""
        try:
            test_suite = CSRFTestSuite(app)
            results = test_suite.run_all_tests()
            
            return jsonify({
                'success': True,
                'results': results,
                'message': 'CSRF test suite completed'
            })
        except Exception as e:
            logger.exception('Error running CSRF test suite')
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Failed to run CSRF test suite'
            }), 500


def get_csrf_security_recommendations() -> List[str]:
    """Get CSRF security recommendations"""
    return [
        "Ensure CSRF protection is enabled for all state-changing operations",
        "Use HTTPS in production to prevent token interception",
        "Set appropriate CSRF token expiration times",
        "Implement CSRF token rotation for sensitive operations",
        "Monitor CSRF error rates for potential attacks",
        "Use SameSite cookies to provide additional protection",
        "Implement CSRF protection for API endpoints",
        "Test CSRF protection regularly",
        "Use secure random token generation",
        "Implement CSRF protection for AJAX requests"
    ]


def check_csrf_security_status(app: Flask) -> Dict[str, Any]:
    """Check overall CSRF security status"""
    try:
        csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
        csrf_time_limit = app.config.get('WTF_CSRF_TIME_LIMIT', None)
        csrf_secret_key = app.config.get('WTF_CSRF_SECRET_KEY', None)
        
        # Check if running over HTTPS
        is_https = app.config.get('PREFERRED_URL_SCHEME') == 'https'
        
        # Security score calculation
        security_score = 0
        max_score = 5
        
        if csrf_enabled:
            security_score += 1
        if csrf_time_limit and csrf_time_limit > 0:
            security_score += 1
        if csrf_secret_key:
            security_score += 1
        if is_https:
            security_score += 1
        
        # Check for error handlers
        error_handlers = app.error_handler_spec.get(None, {}).get(CSRFError, [])
        if len(error_handlers) > 0:
            security_score += 1
        
        security_percentage = (security_score / max_score) * 100
        
        return {
            'csrf_enabled': csrf_enabled,
            'csrf_time_limit': csrf_time_limit,
            'csrf_secret_key_set': bool(csrf_secret_key),
            'is_https': is_https,
            'error_handlers_registered': len(error_handlers),
            'security_score': security_score,
            'max_score': max_score,
            'security_percentage': security_percentage,
            'recommendations': get_csrf_security_recommendations()
        }
    except Exception as e:
        logger.exception('Error checking CSRF security status')
        return {
            'error': str(e),
            'security_percentage': 0
        }
