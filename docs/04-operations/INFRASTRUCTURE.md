# Infrastructure Setup (Phase 1.5)

This guide covers production infrastructure for the Flask boilerplate: backup automation, Redis, Celery (worker + Beat + Flower), logging (Sentry, aggregation), and database indexes.

**See also:** [DEPLOYMENT.md](DEPLOYMENT.md) · [CONFIGURATION.md](CONFIGURATION.md) · [EMAIL_QUEUE_CELERY.md](../03-development/email/EMAIL_QUEUE_CELERY.md)

---

## 1. Backup automation

The app includes `scripts/backup_database.py` for PostgreSQL (plain SQL + pg_dump) and SQLite. Schedule it with cron or a systemd timer.

### Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Daily backup at 2:00 AM (adjust path and venv)
0 2 * * * cd /var/www/boilerplate/app && ./venv/bin/python scripts/backup_database.py >> /var/log/boilerplate/backup.log 2>&1
```

### systemd timer

**Service:** `/etc/systemd/system/boilerplate-backup.service`

```ini
[Unit]
Description=Boilerplate database backup
After=network.target postgresql.service

[Service]
Type=oneshot
User=flaskapp
Group=flaskapp
WorkingDirectory=/var/www/boilerplate/app
Environment="PATH=/var/www/boilerplate/app/venv/bin"
ExecStart=/var/www/boilerplate/app/venv/bin/python scripts/backup_database.py
```

**Timer:** `/etc/systemd/system/boilerplate-backup.timer`

```ini
[Unit]
Description=Run boilerplate backup daily
Requires=boilerplate-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable boilerplate-backup.timer
sudo systemctl start boilerplate-backup.timer
sudo systemctl list-timers
```

Backups are written to `app/data/db/backups/`. Rotate or archive old files (e.g. cron + find or a separate cleanup script).

---

## 2. Redis setup

Used for cache, Celery broker/backend, and optionally Flask session storage.

### Install and run Redis

**Ubuntu/Debian:**

```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**macOS (Homebrew):**

```bash
brew install redis
brew services start redis
```

### Application configuration

In `.env`:

```env
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

- **Cache:** Setting `CACHE_TYPE=redis` and `REDIS_URL` enables Redis for Flask-Caching (see [CONFIGURATION.md](CONFIGURATION.md)).
- **Session (optional):** For Redis-backed Flask session, install `flask-session` and set `SESSION_TYPE=redis` and `SESSION_REDIS` (or derive from `REDIS_URL`). The default is server-side/cookie session; UserSession records are stored in the database.

---

## 3. Celery setup

### Worker

```bash
cd /path/to/app
source venv/bin/activate
celery -A celery_app.celery worker --loglevel=info
```

Production (e.g. systemd): see [EMAIL_QUEUE_CELERY.md](../03-development/email/EMAIL_QUEUE_CELERY.md).

### Beat scheduler

The app defines a Beat schedule in `app/extensions/celery_config.py` (e.g. cleanup expired sessions, role assignments, old email logs). Run Beat once per environment:

```bash
celery -A celery_app.celery beat --loglevel=info
```

Production: run as a separate process/service (e.g. second systemd unit).

### Monitoring with Flower (optional)

```bash
pip install flower
celery -A celery_app.celery flower --port=5555
```

Open `http://localhost:5555`. In production, put Flower behind auth and restrict access.

---

## 4. Database optimization

### Connection pooling

Already supported via config (see [CONFIGURATION.md](CONFIGURATION.md)):

```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Index creation for critical queries

Run the provided script to add recommended indexes (PostgreSQL). It is idempotent (uses `IF NOT EXISTS` where applicable).

```bash
python scripts/add_performance_indexes.py
```

Or run the SQL manually (see script output or `scripts/sql/performance_indexes.sql` if present). Indexes typically include:

- `auth.users`: `email`, `username` (login, lookups)
- `auth.user_sessions`: `user_id`, `expires_at`, `session_token` (session checks, cleanup)
- `auth.failed_login_attempts`: `email`, `attempted_at` (security reports)
- Other high-read tables used in admin/reports

---

## 5. Logging infrastructure

### Structured logging

The app logs to `app/data/logs/` (e.g. `app.log`, `error.log`, `access.log`, `security.log`, `audit.log`). Admins can view logs at **Admin → System → System Logs** (`/admin/logs`).

### Error tracking (Sentry, optional)

Set `SENTRY_DSN` in `.env` (and optionally `SENTRY_ENVIRONMENT=production`). The app will initialize Sentry when the DSN is present. Install the SDK:

```bash
pip install sentry-sdk[flask]
```

Or add to `requirements/requirements-monitoring.txt` and install with that extra.

### Log aggregation and APM

- **ELK / CloudWatch:** Point your log shipper (Filebeat, Fluentd, CloudWatch agent, etc.) at `app/data/logs/` and your existing log files.
- **APM (DataDog, New Relic):** Use each vendor’s Python/Flask agent and configure via their docs and environment variables.

---

## 6. Production environment checklist

- [ ] Server provisioned; firewall and SSH hardened
- [ ] Reverse proxy (Nginx/Apache) and SSL (e.g. Let’s Encrypt) — see [DEPLOYMENT.md](DEPLOYMENT.md)
- [ ] Database: migrations applied, pooling configured, backups scheduled (cron or systemd timer)
- [ ] Redis: installed and running; `REDIS_URL` and `CACHE_TYPE=redis` set if using cache
- [ ] Celery: worker and beat run as separate processes/services; broker/backend use Redis
- [ ] Optional: Flower for Celery monitoring (behind auth)
- [ ] Optional: Sentry DSN set for error tracking
- [ ] Optional: Log aggregation and APM configured for your platform
