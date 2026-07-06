# Getting Started

Installation and setup for the Job Seeker Automation App.

## Prerequisites

- Python 3.12+ (3.8+ supported)
- Git
- PostgreSQL 16 (production/Docker) or SQLite (local dev, default)

Optional for automation features:
- Playwright/Chromium (job scraping and auto-apply)
- OpenAI API key (LLM tailoring)
- Redis + Celery (background tasks, Docker deployments)

## Quick Start (Local — No Docker)

### 1. Clone and set up environment

```bash
git clone <repository-url>
cd boilerplate-job-seeker

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements/requirements.txt -r requirements/requirements-jobs.txt
```

### 2. Configure environment

```bash
cp env.example .env
```

Minimum `.env` settings for local dev:

```env
SECRET_KEY=change-me-in-production
JWT_SECRET_KEY=change-me-in-production
DB_TYPE=sqlite
DB_NAME=app.db
FLASK_ENV=development
FLASK_DEBUG=True
```

Generate secure keys:
```bash
python scripts/generate_secret_key.py
```

### 3. Install Playwright (recommended)

```bash
playwright install chromium
```

On macOS, use system Chrome:
```env
PLAYWRIGHT_CHANNEL=chrome
```

### 4. Initialize database

**Both scripts are required:**

```bash
python scripts/init_database.py      # auth + core tables
python scripts/create_jobs_schema.py # discovery, credentials, batches
```

### 5. Create admin user

```bash
python scripts/create_dev_user.py
```

Defaults: `admin@example.com` / `admin123`

### 6. Run the application

```bash
python run.py
```

Open http://localhost:5000 and log in.

**Local dev does not require Redis, Celery, or Docker.**

## Docker Setup (Production-Style)

```bash
docker compose up --build

# Initialize database (from host or inside container)
python scripts/init_database.py
python scripts/create_jobs_schema.py
python scripts/create_dev_user.py
```

| Service | Port | Purpose |
|---------|------|---------|
| web | 5000 | Flask application |
| db | 5433 | PostgreSQL |
| redis | 6380 | Celery broker |
| celery_worker | — | Background tasks |
| celery_beat | — | Scheduled discovery |

Docker PostgreSQL: `jobseeker` / `jobseeker` / `jobseeker_db` on port 5433.

## First Login

1. Navigate to http://localhost:5000
2. Log in with `admin@example.com` / `admin123`
3. Follow the [First Run Checklist](FIRST_RUN_CHECKLIST.md) to verify everything works

## Optional: Enable Automation

### Credential encryption key

Required before storing LinkedIn/Indeed portal sessions:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:
```env
CREDENTIAL_ENCRYPTION_KEY=<generated-key>
```

### LLM tailoring

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Works without API key (heuristic fallback).

### Discovery APIs

```env
ADZUNA_APP_ID=your-app-id
ADZUNA_APP_KEY=your-app-key
```

See [Automation Setup](../04-operations/AUTOMATION_SETUP.md) for full configuration.

## Project Structure

```
boilerplate-job-seeker/
├── app/
│   ├── __init__.py              # Application factory
│   ├── modules/                 # Feature blueprints
│   │   ├── resume/            # Master profile
│   │   ├── jobs/              # Postings and discovery
│   │   ├── applications/      # Pipeline and tailoring
│   │   ├── apply/             # Pre-fill review
│   │   ├── analytics/         # Metrics
│   │   ├── auth/              # Authentication
│   │   └── admin/             # RBAC admin
│   ├── services/                # Business logic
│   │   ├── discovery/         # Job connectors
│   │   ├── scraping/          # Playwright automation
│   │   ├── apply_adapters/    # Portal submission
│   │   └── ...
│   ├── models/
│   │   ├── auth.py            # Auth schema models
│   │   └── jobs.py            # Jobs schema models
│   ├── templates/               # Jinja2 templates
│   └── static/                  # Vuexy + Tailwind assets
├── config/modules.py            # Sidebar navigation
├── docs/                        # Documentation
├── scripts/                     # Setup and utility scripts
├── tests/                       # pytest suite
├── requirements/                # Split requirement files
├── run.py                       # Development server
├── celery_app.py                # Celery worker entry
└── docker-compose.yml           # Docker stack
```

## Common Tasks

```bash
# Run tests
pytest

# Backup database
python scripts/backup_database.py

# Export portal session
python scripts/export_playwright_storage.py linkedin

# Check database tables
python scripts/check_database_tables.py

# Migrate existing database
python scripts/migrate_jobs_automation.py
```

## Next Steps

### As a job seeker
1. [Upload your resume](../02-user-guide/MASTER_PROFILE.md)
2. [Follow the workflow](../02-user-guide/WORKFLOW.md)
3. [Set up job discovery](../02-user-guide/JOB_DISCOVERY.md)

### As an administrator
1. [Admin Guide](../04-operations/ADMIN_GUIDE.md)
2. [Automation Setup](../04-operations/AUTOMATION_SETUP.md)
3. [First Run Checklist](FIRST_RUN_CHECKLIST.md)

### As a developer
1. [Architecture](../02-architecture/ARCHITECTURE.md)
2. [Job Seeker Services](../02-architecture/JOB_SEEKER_SERVICES.md)
3. [API Reference](../03-development/JOB_SEEKER_API.md)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database tables missing | Run both `init_database.py` and `create_jobs_schema.py` |
| Import errors | Activate venv; install `requirements.txt` + `requirements-jobs.txt` |
| Port in use | `FLASK_RUN_PORT=5001 python run.py` |
| Playwright not found | `playwright install chromium` |
| Discovery features fail | Run `create_jobs_schema.py` |

See [Troubleshooting Guide](../04-operations/TROUBLESHOOTING.md) for more.

## Related Docs

- [First Run Checklist](FIRST_RUN_CHECKLIST.md)
- [User Guide](../02-user-guide/README.md)
- [Configuration](../04-operations/CONFIGURATION.md)
- [00-OVERVIEW](../00-OVERVIEW.md)
