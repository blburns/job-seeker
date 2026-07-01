# Email Queue with Celery

Complete guide to async email sending with Celery and Redis.

---

## Overview

The email queue system provides:
- ✅ Async email sending (non-blocking)
- ✅ Automatic retry with exponential backoff
- ✅ Email delivery tracking
- ✅ Bulk email support
- ✅ Failed email retry
- ✅ Periodic maintenance tasks

---

## Architecture

```
User Action → Task Queue (Redis) → Celery Worker → Email Service → Provider
                                         ↓
                                   Email Log (Database)
```

---

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-celery.txt
```

**Includes:**
- `celery==5.3.4` - Task queue
- `redis==5.0.1` - Message broker
- `flower==2.0.1` - Monitoring (optional)

### 2. Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Configure Environment

Add to `.env`:
```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application URL (for email links)
APP_URL=http://localhost:5000
```

### 4. Run Database Migration

```bash
python scripts/add_email_tables.py
```

Creates:
- `public.email_logs` - Email tracking
- `auth.email_preferences` - User preferences

---

## Running Celery

### Start Celery Worker

```bash
celery -A celery_app.celery worker --loglevel=info
```

**With autoreload (development):**
```bash
watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- \
  celery -A celery_app.celery worker --loglevel=info
```

### Start Celery Beat (Scheduler)

For periodic tasks:
```bash
celery -A celery_app.celery beat --loglevel=info
```

### Start Flower (Monitoring)

```bash
celery -A celery_app.celery flower
```

Access at: `http://localhost:5555`

### Production Setup

Use supervisor or systemd:

**`/etc/supervisor/conf.d/celery.conf`:**
```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A celery_app.celery worker --loglevel=info
directory=/path/to/app
user=www-data
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:celery-beat]
command=/path/to/venv/bin/celery -A celery_app.celery beat --loglevel=info
directory=/path/to/app
user=www-data
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
killasgroup=true
priority=999
```

---

## Usage

### Send Async Email

```python
from app.tasks.email_tasks import send_email_async

# Queue email for async sending
task = send_email_async.delay(
    to_email='user@example.com',
    subject='Welcome!',
    template='welcome',
    context={'user': user}
)

# Get task ID
task_id = task.id

# Check status (optional)
result = task.get(timeout=10)  # Wait up to 10 seconds
```

### Send Bulk Emails

```python
from app.tasks.email_tasks import send_bulk_email_async

recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']

task = send_bulk_email_async.delay(
    recipients=recipients,
    subject='Newsletter',
    template='newsletter',
    context={'month': 'January'}
)
```

### Pre-built Email Tasks

```python
from app.tasks.email_tasks import (
    send_welcome_email,
    send_verification_email,
    send_password_reset_email
)

# Welcome email
send_welcome_email.delay(user_id=str(user.id))

# Verification email
send_verification_email.delay(
    user_id=str(user.id),
    token='verification_token_here'
)

# Password reset
send_password_reset_email.delay(
    user_id=str(user.id),
    token='reset_token_here'
)
```

---

## Email Tracking

### Email Log Model

Every email is logged with:
- Status (queued, sent, failed, bounced)
- Timestamps (sent, delivered, opened, clicked)
- Provider info
- Error messages
- Task ID

### Query Email Logs

```python
from app.models.email_log import EmailLog

# Get user's email history
logs = EmailLog.get_user_emails(user_id=user.id, limit=50)

# Get failed emails
failed = EmailLog.get_failed_emails(hours=24)

# Get by task ID
log = EmailLog.get_by_task_id(task_id='abc-123')
```

### Update Email Status

```python
# Mark as sent
log.mark_sent(provider_message_id='msg_123')

# Mark as delivered
log.mark_delivered()

# Mark as opened
log.mark_opened()

# Mark as bounced
log.mark_bounced(error_message='Invalid email address')
```

---

## Email Preferences

### User Preferences

Users can manage:
- Marketing emails
- Product updates
- Newsletter
- Order notifications
- Account notifications
- Security alerts (always on)
- Email frequency (immediate, daily, weekly)

### Check Preferences

```python
from app.models.email_log import EmailPreference

# Get preferences
prefs = EmailPreference.get_or_create(user_id=user.id)

# Check if can send
if prefs.can_send_email('marketing'):
    send_email_async.delay(...)
```

### Unsubscribe

Users can unsubscribe via:
- Email preferences page: `/users/settings/email-preferences`
- Unsubscribe link in emails: `/unsubscribe/<token>`

**Add to email templates:**
```html
<a href="{{ config.get('APP_URL') }}/unsubscribe/{{ user.email_preference.unsubscribe_token }}">
  Unsubscribe
</a>
```

---

## Periodic Tasks

### Configured Tasks

**Cleanup Tasks (hourly):**
- `cleanup_expired_sessions` - Remove expired sessions
- `cleanup_expired_role_assignments` - Remove expired roles

**Daily Tasks:**
- `cleanup_old_email_logs` - Remove logs older than 90 days
- `send_daily_digest` - Send daily digest emails

### Add Custom Periodic Task

Edit `app/extensions/celery_config.py`:

```python
'beat_schedule': {
    'my-task': {
        'task': 'app.tasks.my_task',
        'schedule': 3600.0,  # Every hour
        'args': (),
    },
}
```

---

## Monitoring

### Flower Dashboard

Access: `http://localhost:5555`

Features:
- Active tasks
- Task history
- Worker status
- Task statistics
- Rate limiting

### Redis CLI

```bash
redis-cli

# Check queue length
LLEN celery

# Monitor commands
MONITOR

# Get all keys
KEYS *
```

### Logs

```bash
# Worker logs
tail -f celery-worker.log

# Beat logs
tail -f celery-beat.log
```

---

## Error Handling

### Automatic Retry

Tasks automatically retry with exponential backoff:
- Retry 1: After 1 minute
- Retry 2: After 2 minutes
- Retry 3: After 4 minutes
- Max retries: 3

### Failed Task Recovery

```python
from app.tasks.maintenance_tasks import retry_failed_emails

# Retry all failed emails from last 24 hours
retry_failed_emails.delay()
```

### Manual Retry

```python
from app.tasks.email_tasks import send_email_async

# Get failed log
log = EmailLog.query.filter_by(status='failed').first()

# Retry
send_email_async.delay(
    to_email=log.to_email,
    subject=log.subject,
    template=log.template,
    context={}
)
```

---

## Performance Tuning

### Worker Concurrency

```bash
# 4 concurrent workers
celery -A celery_app.celery worker --concurrency=4

# Auto-scale (min 2, max 10)
celery -A celery_app.celery worker --autoscale=10,2
```

### Task Priority

```python
# High priority
send_email_async.apply_async(
    args=[...],
    priority=9
)

# Low priority
send_email_async.apply_async(
    args=[...],
    priority=1
)
```

### Rate Limiting

```python
@shared_task(rate_limit='100/m')  # 100 per minute
def send_email_async(...):
    ...
```

---

## Troubleshooting

### Worker Not Processing Tasks

1. Check Redis is running:
   ```bash
   redis-cli ping
   ```

2. Check worker logs:
   ```bash
   celery -A celery_app.celery worker --loglevel=debug
   ```

3. Purge queue:
   ```bash
   celery -A celery_app.celery purge
   ```

### Tasks Timing Out

Increase time limits in `celery_config.py`:
```python
'task_time_limit': 600,  # 10 minutes
'task_soft_time_limit': 540,  # 9 minutes
```

### Memory Issues

```bash
# Restart workers after 1000 tasks
celery -A celery_app.celery worker --max-tasks-per-child=1000
```

---

## Best Practices

1. **Always use `.delay()` or `.apply_async()`**
   - Never call task functions directly in production

2. **Keep tasks idempotent**
   - Tasks should be safe to retry

3. **Use task IDs for tracking**
   - Store task IDs in database for status checking

4. **Set appropriate timeouts**
   - Prevent tasks from running forever

5. **Monitor queue length**
   - Alert if queue grows too large

6. **Use separate queues for different priorities**
   ```python
   send_email_async.apply_async(args=[...], queue='high-priority')
   ```

7. **Log everything**
   - Use structured logging for debugging

---

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)

---

**Email queue system is production-ready!** 🚀
