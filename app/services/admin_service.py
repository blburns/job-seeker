"""
Admin Service
Provides metrics, monitoring, and system health data for admin dashboard
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, and_, or_, text
from sqlalchemy.exc import ProgrammingError
from app.extensions.core import db
from app.models.auth import User, FailedLogin
from app.models.session import UserSession
from app.models.email_log import EmailLog
from app.models.rbac import UserRoleAssignment
from app.services.rbac_service import rbac_service

# Optional psutil import for disk space monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin dashboard metrics and monitoring"""
    
    # ============================================================================
    # User Metrics
    # ============================================================================
    
    @staticmethod
    def get_user_metrics() -> Dict:
        """Get user-related metrics"""
        try:
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            admin_users = User.query.filter_by(is_admin=True).count()
            superadmin_users = User.query.filter_by(is_superadmin=True).count()
            verified_users = User.query.filter_by(email_verified=True).count()
            
            # Users with 2FA enabled
            users_with_2fa = User.query.filter_by(totp_enabled=True).count()
            
            return {
                'total': total_users,
                'active': active_users,
                'inactive': total_users - active_users,
                'admins': admin_users,
                'superadmins': superadmin_users,
                'verified': verified_users,
                'unverified': total_users - verified_users,
                'with_2fa': users_with_2fa,
                '2fa_percentage': round((users_with_2fa / total_users * 100) if total_users > 0 else 0, 1)
            }
        except Exception as e:
            logger.exception("Error getting user metrics")
            db.session.rollback()
            return {}
    
    @staticmethod
    def get_signup_metrics(days: int = 30) -> Dict:
        """Get signup metrics for the last N days"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Signups in period
            signups = User.query.filter(User.created_at >= cutoff).count()
            
            # Daily signups
            daily_signups = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= cutoff
            ).group_by(
                func.date(User.created_at)
            ).order_by('date').all()
            
            # Calculate average
            avg_daily = round(signups / days, 1) if days > 0 else 0
            
            return {
                'total': signups,
                'period_days': days,
                'average_daily': avg_daily,
                'daily_breakdown': [
                    {'date': str(date), 'count': count}
                    for date, count in daily_signups
                ]
            }
        except Exception as e:
            logger.exception("Error getting signup metrics")
            db.session.rollback()
            return {}
    
    @staticmethod
    def get_user_growth_data(months: int = 6) -> List[Dict]:
        """Get user growth data for charts"""
        try:
            cutoff = datetime.utcnow() - timedelta(days=months * 30)
            
            # Monthly user counts
            monthly_data = db.session.query(
                func.date_trunc('month', User.created_at).label('month'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= cutoff
            ).group_by(
                func.date_trunc('month', User.created_at)
            ).order_by('month').all()
            
            # Calculate cumulative
            cumulative = 0
            result = []
            for month, count in monthly_data:
                cumulative += count
                result.append({
                    'month': month.strftime('%Y-%m'),
                    'new_users': count,
                    'total_users': cumulative
                })
            
            return result
        except Exception as e:
            logger.exception("Error getting user growth data")
            db.session.rollback()
            return []
    
    # ============================================================================
    # Session Metrics
    # ============================================================================
    
    @staticmethod
    def get_session_metrics() -> Dict:
        """Get session-related metrics. UserSession has device_info (JSONB), not device_type."""
        try:
            now = datetime.utcnow()

            # Active sessions
            active_sessions = UserSession.query.filter(
                UserSession.expires_at > now
            ).count()

            # Total sessions
            total_sessions = UserSession.query.count()

            # Build by_device from device_info in Python (no device_type column)
            active_list = (
                UserSession.query.filter(UserSession.expires_at > now)
                .all()
            )
            by_device = {}
            for session in active_list:
                name = session.device_name if session.device_info else "Unknown"
                by_device[name] = by_device.get(name, 0) + 1

            return {
                'active': active_sessions,
                'total': total_sessions,
                'expired': total_sessions - active_sessions,
                'by_device': by_device,
            }
        except Exception as e:
            logger.exception("Error getting session metrics")
            db.session.rollback()
            return {}
    
    # ============================================================================
    # Activity Monitoring
    # ============================================================================
    
    @staticmethod
    def get_recent_logins(limit: int = 10) -> List[Dict]:
        """Get recent login activity"""
        try:
            recent_sessions = UserSession.query.order_by(
                UserSession.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    'user_id': str(session.user_id),
                    'username': session.user.username if session.user else 'Unknown',
                    'ip_address': session.ip_address,
                    'device': session.device_name,
                    'browser': (session.device_info or {}).get('browser'),
                    'os': (session.device_info or {}).get('os'),
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                }
                for session in recent_sessions
            ]
        except Exception as e:
            logger.exception("Error getting recent logins")
            db.session.rollback()
            return []
    
    @staticmethod
    def get_failed_login_attempts(hours: int = 24) -> List[Dict]:
        """Get failed login attempts"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            failed_logins = FailedLogin.query.filter(
                FailedLogin.attempted_at >= cutoff
            ).order_by(
                FailedLogin.attempted_at.desc()
            ).all()
            
            return [
                {
                    'username_or_email': log.username_or_email,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'reason': log.reason,
                    'attempted_at': log.attempted_at.isoformat() if log.attempted_at else None
                }
                for log in failed_logins
            ]
        except Exception as e:
            logger.exception("Error getting failed login attempts")
            db.session.rollback()
            return []
    
    @staticmethod
    def get_recent_user_actions(limit: int = 20) -> List[Dict]:
        """Get recent user actions from various sources"""
        try:
            actions = []
            
            # Recent role assignments
            assignments = UserRoleAssignment.query.order_by(
                UserRoleAssignment.assigned_at.desc()
            ).limit(limit).all()
            
            for assignment in assignments:
                actions.append({
                    'type': 'role_assignment',
                    'user': assignment.user.username if assignment.user else 'Unknown',
                    'action': f'Assigned role: {assignment.role.display_name}',
                    'timestamp': assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                    'by': assignment.assigner.username if assignment.assigner else 'System'
                })
            
            # Sort by timestamp
            actions.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
            
            return actions[:limit]
        except Exception as e:
            logger.exception("Error getting recent user actions")
            db.session.rollback()
            return []

    # ============================================================================
    # Email Metrics
    # ============================================================================
    
    @staticmethod
    def get_email_metrics(days: int = 7) -> Dict:
        """Get email sending metrics. Returns empty metrics if email_logs table does not exist."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # Total emails
            total = EmailLog.query.filter(EmailLog.created_at >= cutoff).count()

            # By status
            sent = EmailLog.query.filter(
                EmailLog.created_at >= cutoff,
                EmailLog.status == 'sent'
            ).count()

            failed = EmailLog.query.filter(
                EmailLog.created_at >= cutoff,
                EmailLog.status == 'failed'
            ).count()

            delivered = EmailLog.query.filter(
                EmailLog.created_at >= cutoff,
                EmailLog.status == 'delivered'
            ).count()

            bounced = EmailLog.query.filter(
                EmailLog.created_at >= cutoff,
                EmailLog.status == 'bounced'
            ).count()

            return {
                'total': total,
                'sent': sent,
                'failed': failed,
                'delivered': delivered,
                'bounced': bounced,
                'success_rate': round((sent / total * 100) if total > 0 else 0, 1),
                'period_days': days
            }
        except ProgrammingError as e:
            db.session.rollback()
            logger.warning(
                "Email metrics skipped (table may not exist): %s",
                e.orig if getattr(e, "orig", None) else e,
            )
            return {
                'total': 0,
                'sent': 0,
                'failed': 0,
                'delivered': 0,
                'bounced': 0,
                'success_rate': 0.0,
                'period_days': days
            }
        except Exception as e:
            logger.exception("Error getting email metrics")
            db.session.rollback()
            return {
                'total': 0,
                'sent': 0,
                'failed': 0,
                'delivered': 0,
                'bounced': 0,
                'success_rate': 0.0,
                'period_days': days
            }

    @staticmethod
    def get_email_logs_list(
        page: int = 1,
        per_page: int = 25,
        status: Optional[str] = None,
        days: Optional[int] = None,
    ) -> Dict:
        """
        Get paginated email logs for the admin email logs page.
        Returns items, pagination (total, page, per_page, total_pages), and summary metrics.
        """
        try:
            per_page = max(1, min(100, per_page))
            page = max(1, page)
            query = EmailLog.query
            if days is not None and days > 0:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(EmailLog.created_at >= cutoff)
            if status and str(status).strip().lower() in (
                'queued', 'sent', 'failed', 'delivered', 'bounced'
            ):
                query = query.filter(EmailLog.status == str(status).strip().lower())
            query = query.order_by(EmailLog.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            items = []
            for log in pagination.items:
                items.append({
                    'id': str(log.id),
                    'to_email': log.to_email or '—',
                    'from_email': log.from_email or '—',
                    'subject': (log.subject or '—')[:80],
                    'template': log.template or '—',
                    'status': log.status or '—',
                    'error_message': (log.error_message or '')[:200],
                    'provider': log.provider or '—',
                    'created_at': log.created_at.isoformat() if log.created_at else None,
                    'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                })
            period_days = days if days and days > 0 else 30
            summary = AdminService.get_email_metrics(days=min(period_days, 7))
            return {
                'items': items,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'summary': summary,
                'days_filter': days,
                'status_filter': status,
            }
        except ProgrammingError:
            db.session.rollback()
            return {
                'items': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False,
                'summary': {},
                'days_filter': days,
                'status_filter': status,
            }
        except Exception:
            logger.exception("Error getting email logs list")
            db.session.rollback()
            return {
                'items': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False,
                'summary': {},
                'days_filter': days,
                'status_filter': status,
            }

    @staticmethod
    def get_email_template_list(app) -> List[Dict]:
        """
        List email templates under app/templates/emails/*.html.
        Returns list of {name (stem), filename, path, usage_count}.
        """
        result = []
        root = getattr(app, 'root_path', None) or os.getcwd()
        emails_dir = os.path.join(root, 'templates', 'emails')
        if not os.path.isdir(emails_dir):
            return result
        usage = {}
        try:
            rows = db.session.query(
                EmailLog.template,
                func.count(EmailLog.id).label('count')
            ).filter(
                EmailLog.template.isnot(None),
                EmailLog.template != ''
            ).group_by(EmailLog.template).all()
            usage = {str(t): c for t, c in rows}
        except (ProgrammingError, Exception):
            db.session.rollback()
        for f in sorted(os.listdir(emails_dir)):
            if f.endswith('.html') and not f.startswith('.'):
                name = f[:-5]
                result.append({
                    'name': name,
                    'filename': f,
                    'path': os.path.join(emails_dir, f),
                    'usage_count': usage.get(name, 0),
                })
        return result

    @staticmethod
    def get_email_template_preview_context(app) -> Dict:
        """Sample context for email template preview (no real user/sensitive data)."""
        config = getattr(app, 'config', None) or {}
        base = (config.get('APP_URL') or 'http://localhost:5000').rstrip('/')
        sample_date = datetime(2025, 1, 15, 12, 0, 0)

        # Mock user (username, email for templates that use them)
        class MockUser:
            username = 'sample'
            email = 'sample@example.com'
            def get_full_name(self):
                return 'Sample User'
        user = MockUser()

        # Mock address objects
        class MockAddr:
            def __init__(self, name='Sample User', line1='123 Main St', line2='Apt 1',
                         city='City', state='ST', zip='12345', country='US'):
                self.name = name
                self.line1 = line1
                self.line2 = line2
                self.city = city
                self.state = state
                self.zip = zip
                self.country = country
        billing = MockAddr()
        shipping = MockAddr()

        # Mock invoice (invoice.html)
        class MockInvoiceItem:
            def __init__(self, name='Sample Item', description='Description', quantity=2, unit_price=29.99):
                self.name = name
                self.description = description
                self.quantity = quantity
                self.unit_price = unit_price
        class MockInvoice:
            invoice_number = 'INV-001'
            created_at = due_date = paid_at = sample_date
            billing_address = billing
            items = [MockInvoiceItem(), MockInvoiceItem('Item 2', '', 1, 19.99)]
            subtotal = 69.97
            tax = 7.00
            tax_rate = 10
            discount = 0
            total = 76.97
            status = 'paid'
        invoice = MockInvoice()

        # Mock order (order_confirmation.html, shipping_notification.html)
        class MockOrderItem:
            def __init__(self, name='Product A', quantity=1, price=29.99):
                self.name = name
                self.quantity = quantity
                self.price = price
        class MockOrder:
            order_number = 'ORD-001'
            created_at = sample_date
            total = 49.98
            payment_method = 'Credit Card'
            items = [MockOrderItem(), MockOrderItem('Product B', 2, 9.99)]
            shipping_address = shipping
        order = MockOrder()

        # Mock shipment (shipping_notification.html) – includes items for "Items in This Shipment"
        class MockShipmentItem:
            def __init__(self, name='Product A', quantity=1):
                self.name = name
                self.quantity = quantity
        class MockShipment:
            carrier = 'Sample Carrier'
            tracking_number = '1Z999AA10123456784'
            estimated_delivery = sample_date
            items = [MockShipmentItem('Product A', 1), MockShipmentItem('Product B', 2)]
        shipment = MockShipment()

        # Mock suspension (account_suspension.html)
        class MockSuspension:
            reason = 'Sample reason for preview'
            suspended_at = sample_date
            expires_at = datetime(2025, 2, 15, 12, 0, 0)
            additional_info = 'Additional details for preview.'
        suspension = MockSuspension()

        return {
            'app_name': config.get('APP_NAME', 'Application'),
            'user_name': 'Sample User',
            'user': user,
            'config': config,
            'verification_url': f'{base}/auth/verify-email/sample-token',
            'reset_url': f'{base}/auth/reset-password/sample-token',
            'dashboard_url': f'{base}/admin/dashboard',
            'login_url': f'{base}/auth/login',
            'base_url': base,
            'appeal_url': f'{base}/support/appeal',
            'invoice_url': f'{base}/invoices/sample-123',
            'order_url': f'{base}/orders/sample-456',
            'tracking_url': f'{base}/tracking/sample-789',
            'year': datetime.utcnow().year,
            'expiry_hours': '24',
            'invoice': invoice,
            'order': order,
            'shipment': shipment,
            'suspension': suspension,
        }

    _EMAIL_TEMPLATE_NAME_RE = re.compile(r'^[a-z0-9_]+$')

    @staticmethod
    def get_email_templates_dir(app) -> Optional[str]:
        """Return the absolute path to app/templates/emails or None."""
        root = getattr(app, 'root_path', None) or os.getcwd()
        path = os.path.normpath(os.path.join(root, 'templates', 'emails'))
        return path if os.path.isdir(path) else None

    @staticmethod
    def resolve_email_template_path(app, name: str) -> Optional[str]:
        """
        Resolve path for an email template by name. Only allows names that exist
        in the template list (no path traversal). Returns None if invalid.
        """
        if not name or not str(name).strip():
            return None
        name = str(name).strip().lower()
        if not AdminService._EMAIL_TEMPLATE_NAME_RE.match(name):
            return None
        templates_dir = AdminService.get_email_templates_dir(app)
        if not templates_dir:
            return None
        path = os.path.normpath(os.path.join(templates_dir, name + '.html'))
        if not path.startswith(templates_dir):
            return None
        return path

    @staticmethod
    def read_email_template_content(app, name: str) -> Optional[str]:
        """Read raw content of an email template. Returns None if not found/invalid."""
        path = AdminService.resolve_email_template_path(app, name)
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except OSError:
            return None

    @staticmethod
    def write_email_template_content(app, name: str, content: str) -> bool:
        """Write content to an email template file. Creates file if new. Returns False on error."""
        templates_dir = AdminService.get_email_templates_dir(app)
        if not templates_dir:
            return False
        if not name or not str(name).strip():
            return False
        name = str(name).strip().lower()
        if not AdminService._EMAIL_TEMPLATE_NAME_RE.match(name):
            return False
        path = os.path.normpath(os.path.join(templates_dir, name + '.html'))
        if not path.startswith(templates_dir):
            return False
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except OSError:
            return False

    @staticmethod
    def email_template_exists(app, name: str) -> bool:
        """Return True if an email template file exists for the given name."""
        path = AdminService.resolve_email_template_path(app, name)
        return path is not None and os.path.isfile(path)

    # ============================================================================
    # System Health
    # ============================================================================
    
    @staticmethod
    def check_database_health() -> Dict:
        """Check database connection and health. Rolls back any failed transaction first."""
        try:
            db.session.rollback()
            # Simple query to test connection (SQLAlchemy 2 uses text() for raw SQL)
            db.session.execute(text('SELECT 1'))

            # Get database size (PostgreSQL)
            result = db.session.execute(
                text("SELECT pg_database_size(current_database()) as size")
            ).fetchone()

            db_size = result[0] if result else 0
            db_size_mb = round(db_size / (1024 * 1024), 2)

            return {
                'status': 'healthy',
                'connected': True,
                'size_mb': db_size_mb,
                'message': 'Database connection is healthy'
            }
        except Exception as e:
            logger.exception("Error checking database health")
            db.session.rollback()
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'message': 'Database connection failed'
            }
    
    @staticmethod
    def check_redis_health() -> Dict:
        """Check Redis connection and health. Returns unavailable if Redis is not running."""
        try:
            import redis
            from flask import current_app
            
            redis_url = current_app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            
            # Test connection
            r.ping()
            
            # Get info
            info = r.info()
            
            return {
                'status': 'healthy',
                'connected': True,
                'version': info.get('redis_version'),
                'used_memory_mb': round(info.get('used_memory', 0) / (1024 * 1024), 2),
                'connected_clients': info.get('connected_clients', 0),
                'message': 'Redis connection is healthy'
            }
        except ImportError:
            return {
                'status': 'unavailable',
                'connected': False,
                'message': 'Redis client not installed'
            }
        except Exception as e:
            # Connection refused / not running: treat as unavailable, not a hard error
            try:
                from redis.exceptions import ConnectionError as RedisConnectionError
                if isinstance(e, RedisConnectionError):
                    logger.warning("Redis not available: %s", e)
                    return {
                        'status': 'unavailable',
                        'connected': False,
                        'message': 'Redis not running or connection refused'
                    }
            except ImportError:
                pass
            logger.warning("Redis health check failed: %s", e)
            return {
                'status': 'unavailable',
                'connected': False,
                'error': str(e),
                'message': 'Redis not running or connection refused'
            }
    
    @staticmethod
    def check_celery_health() -> Dict:
        """Check Celery worker and queue health. Returns unavailable if broker (e.g. Redis) is down."""
        try:
            from celery_app import celery
            
            # Check active workers
            inspect = celery.control.inspect()
            active_workers = inspect.active()
            
            if not active_workers:
                return {
                    'status': 'warning',
                    'workers': 0,
                    'message': 'No active Celery workers found'
                }
            
            # Get queue stats
            stats = inspect.stats()
            
            worker_count = len(active_workers)
            total_tasks = sum(len(tasks) for tasks in active_workers.values())
            
            return {
                'status': 'healthy',
                'workers': worker_count,
                'active_tasks': total_tasks,
                'worker_names': list(active_workers.keys()),
                'message': f'{worker_count} worker(s) active'
            }
        except ImportError:
            return {
                'status': 'unavailable',
                'workers': 0,
                'message': 'Celery not configured'
            }
        except Exception as e:
            # Broker (Redis) connection errors: treat as unavailable
            err_str = str(e).lower()
            if 'connection refused' in err_str or 'error 61' in err_str or 'operationalerror' in err_str:
                logger.warning("Celery broker not available: %s", e)
                return {
                    'status': 'unavailable',
                    'workers': 0,
                    'message': 'Celery broker not running (e.g. Redis)'
                }
            logger.exception("Error checking Celery health")
            return {
                'status': 'unhealthy',
                'workers': 0,
                'error': str(e),
                'message': 'Celery check failed'
            }
    
    @staticmethod
    def check_disk_space() -> Dict:
        """Check disk space"""
        if not HAS_PSUTIL:
            return {
                'status': 'unavailable',
                'message': 'psutil not installed'
            }
        
        try:
            disk = psutil.disk_usage('/')
            
            percent_used = disk.percent
            status = 'healthy'
            if percent_used > 90:
                status = 'critical'
            elif percent_used > 80:
                status = 'warning'
            
            return {
                'status': status,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent_used': percent_used,
                'message': f'{percent_used}% disk space used'
            }
        except Exception as e:
            logger.exception("Error checking disk space")
            return {
                'status': 'unknown',
                'error': str(e),
                'message': 'Disk space check failed'
            }
    
    @staticmethod
    def get_system_health() -> Dict:
        """Get overall system health"""
        return {
            'database': AdminService.check_database_health(),
            'redis': AdminService.check_redis_health(),
            'celery': AdminService.check_celery_health(),
            'disk': AdminService.check_disk_space()
        }
    
    # ============================================================================
    # Dashboard Summary
    # ============================================================================
    
    @staticmethod
    def get_dashboard_summary() -> Dict:
        """Get complete dashboard summary"""
        try:
            return {
                'users': AdminService.get_user_metrics(),
                'sessions': AdminService.get_session_metrics(),
                'signups': AdminService.get_signup_metrics(days=30),
                'emails': AdminService.get_email_metrics(days=7),
                'system_health': AdminService.get_system_health(),
                'recent_logins': AdminService.get_recent_logins(limit=10),
                'recent_actions': AdminService.get_recent_user_actions(limit=10),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.exception("Error getting dashboard summary")
            db.session.rollback()
            return {}

    # ============================================================================
    # Reports (aggregated data for admin/reports page)
    # ============================================================================

    @staticmethod
    def get_reports_data(period_days: int = 30) -> Dict:
        """
        Get aggregated report data for the admin reports page.
        period_days: 7, 30, or 90 for time-based metrics.
        """
        try:
            period_days = max(7, min(90, period_days))
            email_days = min(period_days, 7)

            users = AdminService.get_user_metrics()
            signups = AdminService.get_signup_metrics(days=period_days)
            sessions = AdminService.get_session_metrics()
            emails = AdminService.get_email_metrics(days=email_days)

            # Failed logins count for period
            cutoff = datetime.utcnow() - timedelta(days=period_days)
            failed_count = FailedLogin.query.filter(
                FailedLogin.attempted_at >= cutoff
            ).count()
            failed_recent = AdminService.get_failed_login_attempts(
                hours=min(168, period_days * 24)
            )[:20]

            try:
                rbac_stats = rbac_service.get_statistics()
            except Exception:
                logger.exception("Error getting RBAC statistics for reports")
                db.session.rollback()
                rbac_stats = {}

            user_growth = AdminService.get_user_growth_data(
                months=min(6, max(1, period_days // 30))
            )

            return {
                'users': users,
                'signups': signups,
                'sessions': sessions,
                'emails': emails,
                'security': {
                    'failed_login_count': failed_count,
                    'failed_recent': failed_recent,
                    'period_days': period_days,
                },
                'rbac': rbac_stats,
                'user_growth': user_growth,
                'period_days': period_days,
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception:
            logger.exception("Error getting reports data")
            db.session.rollback()
            fallback_days = 30
            return {
                'users': {},
                'signups': {},
                'sessions': {},
                'emails': {},
                'security': {
                    'failed_login_count': 0,
                    'failed_recent': [],
                    'period_days': fallback_days,
                },
                'rbac': {},
                'user_growth': [],
                'period_days': fallback_days,
                'timestamp': None,
            }


    # ============================================================================
    # Settings display (read-only config for admin/settings page)
    # ============================================================================

    @staticmethod
    def get_settings_display_config(app) -> Dict:
        """
        Build a safe, display-only view of application config for the admin settings page.
        Secrets are masked; values come from Flask config (env). Changes require .env edit and restart.
        """
        from app.services.automation_kill_switch import (
            file_kill_switch_enabled,
            is_automation_disabled,
            kill_switch_source,
        )

        config = getattr(app, 'config', None) or {}
        get_ = lambda k, default=None: config.get(k, default)

        def mask_secret(val):
            if val is None or str(val).strip() == '':
                return 'Not set'
            return '••••••••' if len(str(val)) > 4 else '••••'

        def yes_no(val):
            if val is None:
                return '—'
            return 'Yes' if val else 'No'

        db_info = get_('DATABASE_INFO') or {}
        db_name = db_info.get('name') or get_('DB_NAME') or '—'
        db_type = get_('DATABASE_TYPE') or get_('DB_TYPE') or '—'

        # OAuth: configured if both client id and secret are set
        oauth_google = 'Configured' if (get_('GOOGLE_CLIENT_ID') and get_('GOOGLE_CLIENT_SECRET')) else 'Not configured'
        oauth_microsoft = 'Configured' if (get_('MICROSOFT_CLIENT_ID') and get_('MICROSOFT_CLIENT_SECRET')) else 'Not configured'
        oauth_github = 'Configured' if (get_('GITHUB_CLIENT_ID') and get_('GITHUB_CLIENT_SECRET')) else 'Not configured'

        return {
            'general': [
                ('Application name', get_('APP_NAME') or '—'),
                ('Application version', get_('APP_VERSION') or '—'),
                ('Company name', get_('COMPANY_NAME') or '—'),
                ('Environment', get_('FLASK_ENV') or '—'),
                ('Debug mode', yes_no(get_('FLASK_DEBUG'))),
            ],
            'security': [
                ('Secret key', mask_secret(get_('SECRET_KEY'))),
                ('JWT secret key', mask_secret(get_('JWT_SECRET_KEY'))),
                ('CSRF protection', yes_no(get_('WTF_CSRF_ENABLED'))),
            ],
            'database': [
                ('Database type', str(db_type)),
                ('Database name', str(db_name)),
                ('Pool size', str(get_('DB_POOL_SIZE') or '—')),
            ],
            'cache': [
                ('Cache type', get_('CACHE_TYPE') or '—'),
                ('Redis URL', 'Set' if get_('CACHE_REDIS_URL') else 'Not set'),
            ],
            'email': [
                ('Mail server', get_('MAIL_SERVER') or '—'),
                ('Mail port', str(get_('MAIL_PORT') or '—')),
                ('Use TLS', yes_no(get_('MAIL_USE_TLS'))),
                ('Default sender', get_('MAIL_DEFAULT_SENDER') or '—'),
                ('Mail username', 'Set' if get_('MAIL_USERNAME') else 'Not set'),
                ('Mail password', 'Set' if get_('MAIL_PASSWORD') else 'Not set'),
                ('Email provider', get_('EMAIL_PROVIDER') or '—'),
            ],
            'oauth': [
                ('Google', oauth_google),
                ('Microsoft', oauth_microsoft),
                ('GitHub', oauth_github),
            ],
            'logging': [
                ('Log level', get_('LOG_LEVEL') or '—'),
                ('Log file', get_('LOG_FILE') or '—'),
            ],
            'automation': [
                (
                    'Apply automation enabled',
                    yes_no(os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() in ('true', '1', 'yes')),
                ),
                (
                    'Automation kill switch',
                    (
                        f'ON ({kill_switch_source()}) — all auto-submit blocked'
                        if is_automation_disabled()
                        else 'Off'
                    ),
                ),
                (
                    'File kill switch (no restart)',
                    yes_no(file_kill_switch_enabled()),
                ),
                ('Daily apply cap', os.getenv('DAILY_APPLY_CAP', '25')),
                (
                    'LinkedIn scrape',
                    yes_no(os.getenv('LINKEDIN_SCRAPE_ENABLED', 'false').lower() in ('true', '1', 'yes')),
                ),
                (
                    'Indeed scrape',
                    yes_no(os.getenv('INDEED_SCRAPE_ENABLED', 'false').lower() in ('true', '1', 'yes')),
                ),
                (
                    'LLM provider',
                    (
                        'Gemini (Google AI Studio)'
                        if (
                            (os.getenv('LLM_PROVIDER', 'auto').lower() == 'gemini'
                             and (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')))
                            or (
                                os.getenv('LLM_PROVIDER', 'auto').lower() in ('auto', '')
                                and (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
                            )
                        )
                        else (
                            'OpenAI'
                            if os.getenv('OPENAI_API_KEY')
                            else 'None (heuristic)'
                        )
                    ),
                ),
                (
                    'OpenAI API key',
                    'Set' if os.getenv('OPENAI_API_KEY') else 'Not set',
                ),
                (
                    'Gemini / Google AI Studio key',
                    'Set'
                    if (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))
                    else 'Not set',
                ),
            ],
        }

    # ============================================================================
    # System logs (tail log file for admin log viewer)
    # ============================================================================

    _LOG_LEVELS = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    _MAX_TAIL_LINES = 2000
    # Allowed log files under app/data/logs/ (name only, .log appended)
    ALLOWED_LOG_FILES = (
        ('access', 'Access'),
        ('app', 'App'),
        ('error', 'Error'),
        ('security', 'Security'),
        ('audit', 'Audit'),
    )

    @staticmethod
    def _resolve_log_path(app, log_name: str) -> Optional[str]:
        """
        Resolve path for a named log file under app/data/logs/.
        Only allows names in ALLOWED_LOG_FILES. Returns None if invalid.
        """
        allowed = {t[0] for t in AdminService.ALLOWED_LOG_FILES}
        if not log_name or str(log_name).strip().lower() not in allowed:
            return None
        log_name = str(log_name).strip().lower()
        root = getattr(app, 'root_path', None) or os.getcwd()
        return os.path.normpath(os.path.join(root, 'data', 'logs', log_name + '.log'))

    @staticmethod
    def _extract_level(line: str) -> Optional[str]:
        """Extract log level from a line (e.g. '2025-01-31 12:00:00,000 INFO: ...')."""
        # Match " LEVEL: " or " LEVEL " after optional timestamp
        m = re.search(r'\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*[:\s]', line, re.IGNORECASE)
        return m.group(1).upper() if m else None

    @staticmethod
    def get_log_tail(
        app,
        log_name: str = 'app',
        lines: int = 500,
        level_filter: Optional[str] = None,
    ) -> Dict:
        """
        Read the last N lines from a named log file under app/data/logs/.
        Only allows names in ALLOWED_LOG_FILES. Returns dict with log_file,
        entries (list of {raw, level}), total_read, error.
        """
        result = {
            'log_file': None,
            'entries': [],
            'total_read': 0,
            'error': None,
        }
        path = AdminService._resolve_log_path(app, log_name)
        if not path:
            result['error'] = 'Invalid or disallowed log file.'
            return result
        result['log_file'] = path
        lines = max(1, min(lines, AdminService._MAX_TAIL_LINES))
        if level_filter:
            level_filter = level_filter.upper()
            if level_filter not in AdminService._LOG_LEVELS:
                level_filter = None
        try:
            if not os.path.exists(path):
                result['error'] = 'Log file does not exist yet.'
                return result
            max_bytes = 2 * 1024 * 1024  # 2MB cap
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(0, 2)
                size = f.tell()
                if size == 0:
                    return result
                start = max(0, size - max_bytes)
                f.seek(start)
                if start > 0:
                    f.readline()  # discard partial line
                raw = f.read()
            all_lines = raw.splitlines()
            if len(all_lines) > lines:
                all_lines = all_lines[-lines:]
            result['total_read'] = len(all_lines)
            for raw_line in all_lines:
                level = AdminService._extract_level(raw_line)
                if level_filter and level != level_filter:
                    continue
                result['entries'].append({'raw': raw_line, 'level': level or 'INFO'})
        except PermissionError:
            result['error'] = 'Permission denied reading log file.'
        except OSError as e:
            result['error'] = f'Could not read log file: {e}'
        except Exception as e:
            logger.exception('Error reading log file')
            result['error'] = str(e)
        return result


# Global admin service instance
admin_service = AdminService()
