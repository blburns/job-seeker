"""
Email Tasks
Async email sending tasks using Celery
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from celery import shared_task
from app.extensions.core import db
from app.models.email_log import EmailLog
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_email_async(self, to_email: str, subject: str, template: str, 
                     context: Dict = None, from_email: str = None) -> Dict:
    """
    Send email asynchronously
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        template: Template name (without .html extension)
        context: Template context variables
        from_email: Sender email address (optional)
    
    Returns:
        dict: Result with success status and message
    """
    try:
        logger.info(f"Sending async email to {to_email}: {subject}")
        
        # Send email
        success = email_service.send_email(
            to_email=to_email,
            subject=subject,
            template=template,
            context=context or {},
            from_email=from_email
        )
        
        # Log email
        log_email(
            to_email=to_email,
            subject=subject,
            template=template,
            status='sent' if success else 'failed',
            task_id=self.request.id
        )
        
        if success:
            return {
                'success': True,
                'message': f'Email sent to {to_email}',
                'task_id': self.request.id
            }
        else:
            raise Exception('Email sending failed')
            
    except Exception as e:
        logger.exception(f"Error sending email to {to_email}")
        
        # Log failed email
        log_email(
            to_email=to_email,
            subject=subject,
            template=template,
            status='failed',
            error_message=str(e),
            task_id=self.request.id
        )
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email to {to_email}")
            return {
                'success': False,
                'message': f'Failed to send email after {self.max_retries} retries',
                'error': str(e)
            }


@shared_task(bind=True)
def send_bulk_email_async(self, recipients: List[str], subject: str, 
                          template: str, context: Dict = None) -> Dict:
    """
    Send bulk emails asynchronously
    
    Args:
        recipients: List of recipient email addresses
        subject: Email subject
        template: Template name
        context: Template context variables
    
    Returns:
        dict: Result with counts of sent/failed emails
    """
    try:
        logger.info(f"Sending bulk email to {len(recipients)} recipients")
        
        sent_count = 0
        failed_count = 0
        
        for to_email in recipients:
            try:
                # Send individual email (could be optimized with batch sending)
                send_email_async.delay(
                    to_email=to_email,
                    subject=subject,
                    template=template,
                    context=context
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue email for {to_email}: {e}")
                failed_count += 1
        
        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': len(recipients)
        }
        
    except Exception as e:
        logger.exception("Error in bulk email sending")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_welcome_email(user_id: str) -> Dict:
    """Send welcome email to new user"""
    from app.models.auth import User
    
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        return send_email_async.delay(
            to_email=user.email,
            subject='Welcome to Our Platform!',
            template='welcome',
            context={'user': user}
        ).get()
        
    except Exception as e:
        logger.exception(f"Error sending welcome email to user {user_id}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_verification_email(user_id: str, token: str) -> Dict:
    """Send email verification email"""
    from app.models.auth import User
    from flask import url_for
    
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Note: url_for won't work in Celery context without _external=True
        # You may need to construct the URL manually or pass it as a parameter
        verification_url = f"{email_service.app.config.get('APP_URL', 'http://localhost:5000')}/auth/verify-email/{token}"
        
        return send_email_async.delay(
            to_email=user.email,
            subject='Verify Your Email Address',
            template='verify_email',
            context={
                'user': user,
                'verification_url': verification_url,
                'token': token
            }
        ).get()
        
    except Exception as e:
        logger.exception(f"Error sending verification email to user {user_id}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_password_reset_email(user_id: str, token: str) -> Dict:
    """Send password reset email"""
    from app.models.auth import User
    
    try:
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        reset_url = f"{email_service.app.config.get('APP_URL', 'http://localhost:5000')}/auth/reset-password/{token}"
        
        return send_email_async.delay(
            to_email=user.email,
            subject='Reset Your Password',
            template='password_reset',
            context={
                'user': user,
                'reset_url': reset_url,
                'token': token
            }
        ).get()
        
    except Exception as e:
        logger.exception(f"Error sending password reset email to user {user_id}")
        return {'success': False, 'error': str(e)}


def log_email(to_email: str, subject: str, template: str, status: str,
              error_message: str = None, task_id: str = None) -> None:
    """
    Log email sending attempt
    
    Args:
        to_email: Recipient email
        subject: Email subject
        template: Template used
        status: Status (sent, failed, queued)
        error_message: Error message if failed
        task_id: Celery task ID
    """
    try:
        email_log = EmailLog(
            to_email=to_email,
            subject=subject,
            template=template,
            status=status,
            error_message=error_message,
            task_id=task_id,
            sent_at=datetime.utcnow() if status == 'sent' else None
        )
        db.session.add(email_log)
        db.session.commit()
    except Exception as e:
        logger.exception("Error logging email")
        db.session.rollback()
