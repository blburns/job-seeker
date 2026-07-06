# Administrator Guide

System administration for the Job Seeker Automation App — user management, automation configuration, deployment, and monitoring.

## Prerequisites

- Application installed — see [GETTING_STARTED.md](../01-getting-started/GETTING_STARTED.md)
- Admin or superadmin account

## Admin Panel

Access the admin panel at `/admin` (requires `admin.access` permission or admin/superadmin role).

### Available sections

| Section | Route | Purpose |
|---------|-------|---------|
| Dashboard | `/admin/dashboard` | System overview |
| Roles | `/admin/roles` | Manage RBAC roles |
| Permissions | `/admin/permissions` | View and assign permissions |
| Settings | `/admin/settings` | Read-only config view (sensitive values masked) |
| System Logs | `/admin/logs` | Application log viewer |
| Email Templates | `/admin/email/templates` | Manage email templates |
| Developer Sitemap | `/admin/developer/sitemap` | All registered routes |

See [RBAC_GUIDE.md](../03-development/rbac/RBAC_GUIDE.md) for permission details.

## User Management

### Create development admin

```bash
python scripts/create_dev_user.py
```

Defaults: `admin@example.com` / `admin123`

Override with environment variables:
```bash
DEV_USER_EMAIL=you@example.com DEV_USER_PASSWORD=securepass python scripts/create_dev_user.py
```

### Create production users

```bash
python scripts/create_user.py
```

Interactive prompts for email, password, and role assignment.

### Seed roles and groups

```bash
python scripts/create_default_roles_groups.py
```

Creates default roles: `superadmin`, `admin`, `manager`, `user`, `guest`.

### Manage permissions

```bash
# View current permissions
python scripts/manage_permissions.py --show

# Emergency permission reset
python scripts/manage_permissions.py --restore-safe

# List admin users
python scripts/check_admins.py
```

### Account utilities

```bash
python scripts/manage_default_accounts.py list
```

## Database Administration

### Initial setup (required for new installs)

```bash
python scripts/init_database.py      # auth + core tables
python scripts/create_jobs_schema.py # discovery, credentials, batches
python scripts/create_dev_user.py    # admin user
```

**Critical:** Both `init_database.py` and `create_jobs_schema.py` are required. The first creates auth and basic jobs tables; the second creates discovery, credential, and batch automation tables.

### Backup

```bash
python scripts/backup_database.py
```

Backups saved to `app/data/db/backups/`.

### Database inspection

```bash
python scripts/check_database_tables.py
python scripts/db_manager.py
```

### Schema migration (existing databases)

```bash
python scripts/migrate_jobs_automation.py
```

Idempotent column additions for databases created before automation features.

### PostgreSQL schemas

| Schema | Contents |
|--------|----------|
| `auth` | users, roles, groups, permissions |
| `jobs` | All job seeker tables |

SQLite uses flat tables without schema prefixes.

## Automation Administration

Full setup guide: [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)

### Quick reference

| Task | Command or setting |
|------|-------------------|
| Generate credential encryption key | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| Export LinkedIn session | `python scripts/export_playwright_storage.py linkedin` |
| Export Indeed session | `python scripts/export_playwright_storage.py indeed` |
| Enable LinkedIn scraping | `LINKEDIN_SCRAPE_ENABLED=true` |
| Enable Indeed scraping | `INDEED_SCRAPE_ENABLED=true` |
| Enable auto-apply | `APPLY_AUTOMATION_ENABLED=true` (+ portal-specific flags) |
| Set daily apply cap | `DAILY_APPLY_CAP=25` |
| Configure LLM | `OPENAI_API_KEY=sk-...` |

### Safety defaults

All automation flags default to **disabled**:

```env
APPLY_AUTOMATION_ENABLED=false
LINKEDIN_AUTO_APPLY_ENABLED=false
INDEED_AUTO_APPLY_ENABLED=false
LINKEDIN_SCRAPE_ENABLED=false
INDEED_SCRAPE_ENABLED=false
```

Enable only when credentials are configured and tested.

## Deployment Modes

### Local development

```bash
cp env.example .env
pip install -r requirements/requirements.txt -r requirements/requirements-jobs.txt
playwright install chromium
python scripts/init_database.py
python scripts/create_jobs_schema.py
python scripts/create_dev_user.py
python run.py
```

- SQLite database (`app.db`)
- No Redis or Celery required
- Discovery runs in Flask process
- Access at http://localhost:5000

### Docker production

```bash
docker compose up --build
python scripts/init_database.py
python scripts/create_jobs_schema.py
python scripts/create_dev_user.py
```

| Service | Port | Purpose |
|---------|------|---------|
| web | 5000 | Flask application |
| db | 5433 | PostgreSQL 16 |
| redis | 6380 | Celery broker and cache |
| celery_worker | — | Background tasks (scraping queue) |
| celery_beat | — | Scheduled discovery runs |

Docker PostgreSQL credentials: `jobseeker` / `jobseeker` / `jobseeker_db`

See [DEPLOYMENT.md](DEPLOYMENT.md) for production server setup.

## Monitoring

### Health endpoints

```bash
curl http://localhost:5000/health
curl http://localhost:5000/health/database
```

### Logs

- Application logs: `app/data/logs/` or `logs/app.log`
- Admin log viewer: `/admin/logs`
- Scrape proofs: `instance/scrape_proofs/`

### Error tracking (optional)

```env
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
```

### Celery monitoring

```bash
# Check worker status (Docker)
docker compose logs celery_worker

# Flower dashboard (if configured)
# http://localhost:5555
```

## Security Hardening

### Production checklist

- [ ] Change `SECRET_KEY` and `JWT_SECRET_KEY` from defaults
- [ ] Set `CREDENTIAL_ENCRYPTION_KEY` (persistent Fernet key)
- [ ] Set `FLASK_DEBUG=False` and `FLASK_ENV=production`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS via reverse proxy
- [ ] Review RBAC role assignments
- [ ] Keep auto-apply flags disabled until tested
- [ ] Set reasonable `DAILY_APPLY_CAP`
- [ ] Configure email for password reset
- [ ] Set up database backups

### Credential security

Portal credentials (LinkedIn, Indeed sessions) are encrypted at rest with Fernet symmetric encryption. The encryption key (`CREDENTIAL_ENCRYPTION_KEY`) must be:
- Generated once and stored securely in `.env`
- Never committed to version control
- The same across all app instances and restarts

Without a persistent key, credentials use an ephemeral per-process key and are lost on restart.

## Optional Features

### Two-factor authentication

```bash
pip install -r requirements/requirements-2fa.txt
python scripts/add_2fa_fields.py
```

See [TWO_FACTOR_AUTH.md](../03-development/auth/TWO_FACTOR_AUTH.md).

### OAuth (Google, Microsoft, GitHub)

```bash
pip install -r requirements/requirements-oauth.txt
python scripts/add_oauth_table.py
```

Configure client IDs in `.env`. See [OAUTH_INTEGRATION.md](../03-development/auth/OAUTH_INTEGRATION.md).

### Email

```env
EMAIL_PROVIDER=console   # Development (prints to console)
EMAIL_PROVIDER=sendgrid  # Production
EMAIL_PROVIDER=smtp      # Custom SMTP
```

See [EMAIL_SERVICE_SETUP.md](../03-development/email/EMAIL_SERVICE_SETUP.md).

## Related Docs

- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) — Detailed automation configuration
- [CONFIGURATION.md](CONFIGURATION.md) — All environment variables
- [DEPLOYMENT.md](DEPLOYMENT.md) — Production deployment
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Problem solving
- [RBAC_GUIDE.md](../03-development/rbac/RBAC_GUIDE.md) — Permission system
- [GETTING_STARTED.md](../01-getting-started/GETTING_STARTED.md) — Initial setup
