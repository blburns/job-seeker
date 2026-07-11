# Quick Reference

## Application

```bash
# Run development server
python run.py

# Run with specific host/port
FLASK_RUN_HOST=0.0.0.0 FLASK_RUN_PORT=5001 python run.py
```

## Database Setup

```bash
# Initial setup (both required)
python scripts/init_database.py
python scripts/create_jobs_schema.py

# Create dev admin user
python scripts/create_dev_user.py

# Migrate existing database
python scripts/migrate_jobs_automation.py

# Backup
python scripts/backup_database.py

# Inspect tables
python scripts/check_database_tables.py
```

## Job Seeker Automation

```bash
# Install Playwright
playwright install chromium

# Generate credential encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Export portal sessions
python scripts/export_playwright_storage.py linkedin
python scripts/export_playwright_storage.py indeed
```

## Testing

```bash
# All tests
pytest

# Job seeker tests
pytest tests/test_indeed_scraper.py tests/test_job_detail_enrichment.py -v
pytest tests/test_tailoring_diff_service.py tests/test_resume_export_service.py -v
pytest tests/test_apply_draft_service.py -v
```

## Celery (Docker/production)

```bash
# Worker
celery -A celery_app.celery worker --loglevel=info -Q scraping,default

# Beat (scheduled discovery)
celery -A celery_app.celery beat --loglevel=info

# Docker
docker compose up --build
docker compose logs celery_worker
```

## Job Seeker Environment Variables

```env
# Required for portal credentials
CREDENTIAL_ENCRYPTION_KEY=<fernet-key>

# LLM tailoring (optional)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Discovery APIs
ADZUNA_APP_ID=
ADZUNA_APP_KEY=

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_CHANNEL=chrome
INDEED_PLAYWRIGHT_HEADLESS=false

# Scraping (default: disabled)
LINKEDIN_SCRAPE_ENABLED=false
INDEED_SCRAPE_ENABLED=false
SCRAPE_RATE_LIMIT_PER_HOUR=20

# Auto-apply (default: disabled)
APPLY_AUTOMATION_ENABLED=false
LINKEDIN_AUTO_APPLY_ENABLED=false
INDEED_AUTO_APPLY_ENABLED=false
DAILY_APPLY_CAP=25
```

Full reference: [CONFIGURATION.md](04-operations/CONFIGURATION.md)

## Job Seeker Routes

### Web UI

```
/                                    → Dashboard
/resume/upload                       → Upload resume
/resume/profiles                     → Master profiles
/jobs/postings                       → Job postings
/jobs/search-profiles                → Search profiles
/jobs/inbox                          → Discovery inbox
/applications/list                   → All applications
/applications/pipeline               → Kanban board
/applications/queue                  → Apply queue
/applications/batches                → Apply batches
/applications/<id>/tailoring         → Tailoring review
/apply/<id>                          → Apply draft review
/apply/credentials                   → Portal credentials
/analytics/                          → Metrics dashboard
```

### API

```
GET    /api/v1/resume/profiles                    → List profiles
POST   /api/v1/resume/upload                      → Parse resume
POST   /api/v1/resume/profiles                    → Save profile
GET    /api/v1/jobs/postings                      → List postings
POST   /api/v1/jobs/search-profiles/<id>/run      → Run discovery
GET    /api/v1/jobs/inbox                         → Discovery inbox
POST   /api/v1/jobs/inbox/<id>/accept             → Accept job
GET    /api/v1/applications/pipeline              → Pipeline view
POST   /api/v1/applications/<id>/tailor          → Tailor resume
POST   /api/v1/applications/<id>/approve          → Approve resume
POST   /api/v1/apply/batches                      → Create batch
POST   /api/v1/apply/batches/<id>/approve         → Approve batch
```

Swagger UI: `/api/v1/docs/`

## Application Stages

```
saved → tailoring → ready_to_apply → applied → phone_screen → interview → offer
                                                      ↘ rejected / withdrawn
```

## Database Schemas

```
auth/                    → users, roles, groups, permissions
jobs/                    → master_profiles, job_postings, applications,
                           resume_versions, apply_drafts, discovered_jobs,
                           portal_credentials, apply_batches
```

## User Management

```bash
python scripts/create_dev_user.py          # admin@example.com / admin123
python scripts/create_user.py              # Interactive
python scripts/create_default_roles_groups.py
python scripts/manage_permissions.py --show
python scripts/check_admins.py
```

## Health Checks

```bash
curl http://localhost:5000/health
curl http://localhost:5000/health/database
curl http://localhost:5000/api/v1/health
```

## File Locations

```
Configuration:     .env
Logs:              app/data/logs/
Scrape proofs:     instance/scrape_proofs/
Submission proofs: instance/submission_proofs/
Models:            app/models/jobs.py
Services:          app/services/
Routes:            app/modules/*/routes.py
API:               app/modules/*/api.py
Scripts:           scripts/
Tests:             tests/
Templates:         app/templates/modules/
```

## See Full Documentation

- [00-OVERVIEW.md](00-OVERVIEW.md) — Application overview
- [README.md](README.md) — Documentation index
- [User Guide](02-user-guide/README.md) — End-user guides
- [JOB_SEEKER_API.md](03-development/JOB_SEEKER_API.md) — API reference
