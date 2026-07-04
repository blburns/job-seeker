"""
Celery Tasks
Background tasks for async processing
"""

from app.tasks.email_tasks import (
    send_email_async,
    send_bulk_email_async,
    send_welcome_email,
    send_verification_email,
    send_password_reset_email
)

from app.tasks.maintenance_tasks import (
    cleanup_expired_sessions,
    cleanup_expired_role_assignments,
    cleanup_old_email_logs
)

from app.tasks.job_tasks import (
    run_discovery_for_profile,
    run_all_active_discoveries,
    batch_tailor_applications,
    submit_apply_batch,
    check_follow_up_reminders,
    check_portal_sessions,
)

__all__ = [
    'send_email_async',
    'send_bulk_email_async',
    'send_welcome_email',
    'send_verification_email',
    'send_password_reset_email',
    'cleanup_expired_sessions',
    'cleanup_expired_role_assignments',
    'cleanup_old_email_logs',
    'run_discovery_for_profile',
    'run_all_active_discoveries',
    'batch_tailor_applications',
    'submit_apply_batch',
    'check_follow_up_reminders',
    'check_portal_sessions',
]
