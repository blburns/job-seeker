"""
Maintenance Tasks
Periodic cleanup and maintenance tasks
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task
from app.extensions.core import db

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """Clean up expired user sessions"""
    try:
        from app.models.session import UserSession
        
        # Find expired sessions
        expired = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired)
        
        # Delete expired sessions
        for session in expired:
            db.session.delete(session)
        
        db.session.commit()
        
        logger.info(f"Cleaned up {count} expired sessions")
        return {'success': True, 'cleaned': count}
        
    except Exception as e:
        logger.exception("Error cleaning up expired sessions")
        db.session.rollback()
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_expired_role_assignments():
    """Clean up expired role assignments"""
    try:
        from app.services.rbac_service import rbac_service
        
        count = rbac_service.cleanup_expired_assignments()
        
        logger.info(f"Cleaned up {count} expired role assignments")
        return {'success': True, 'cleaned': count}
        
    except Exception as e:
        logger.exception("Error cleaning up expired role assignments")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_email_logs():
    """Clean up old email logs (older than 90 days)"""
    try:
        from app.models.email_log import EmailLog
        
        # Delete logs older than 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        old_logs = EmailLog.query.filter(
            EmailLog.created_at < cutoff
        ).all()
        
        count = len(old_logs)
        
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        
        logger.info(f"Cleaned up {count} old email logs")
        return {'success': True, 'cleaned': count}
        
    except Exception as e:
        logger.exception("Error cleaning up old email logs")
        db.session.rollback()
        return {'success': False, 'error': str(e)}


@shared_task
def send_daily_digest():
    """Send daily digest emails to subscribed users"""
    try:
        from app.models.auth import User
        from app.models.email_log import EmailPreference
        from app.tasks.email_tasks import send_email_async
        
        # Find users who want daily digests
        users = User.query.join(EmailPreference).filter(
            EmailPreference.email_frequency == 'daily',
            EmailPreference.unsubscribed_all == False,
            User.is_active == True
        ).all()
        
        sent_count = 0
        
        for user in users:
            try:
                send_email_async.delay(
                    to_email=user.email,
                    subject='Your Daily Digest',
                    template='daily_digest',
                    context={'user': user}
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send digest to {user.email}: {e}")
        
        logger.info(f"Sent {sent_count} daily digest emails")
        return {'success': True, 'sent': sent_count}
        
    except Exception as e:
        logger.exception("Error sending daily digests")
        return {'success': False, 'error': str(e)}


@shared_task
def retry_failed_emails():
    """Retry failed emails from the last 24 hours"""
    try:
        from app.models.email_log import EmailLog
        from app.tasks.email_tasks import send_email_async
        
        # Get failed emails from last 24 hours
        failed_emails = EmailLog.get_failed_emails(hours=24)
        
        retried_count = 0
        
        for email_log in failed_emails:
            try:
                # Only retry once
                if email_log.error_message and 'retry' not in email_log.error_message.lower():
                    send_email_async.delay(
                        to_email=email_log.to_email,
                        subject=email_log.subject,
                        template=email_log.template,
                        context={}
                    )
                    retried_count += 1
            except Exception as e:
                logger.error(f"Failed to retry email {email_log.id}: {e}")
        
        logger.info(f"Retried {retried_count} failed emails")
        return {'success': True, 'retried': retried_count}
        
    except Exception as e:
        logger.exception("Error retrying failed emails")
        return {'success': False, 'error': str(e)}
