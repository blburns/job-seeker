# Configuration Guide

## Overview

This application uses environment variables for configuration, loaded from `.env` files and system environment variables.

## Environment Files

### `.env`
Main configuration file (not committed to git).

### `.env.local`
Local overrides (not committed to git). Overrides `.env` values.

### `env.example`
Example configuration file (committed to git). Copy to `.env` and customize.

## Configuration Loading Order

1. `.env` file (project root)
2. `.env.local` file (if exists, overrides `.env`)
3. System environment variables (override all)

**Viewing configuration (read-only):** Admins can see the effective configuration (grouped by section: General, Security, Database, Cache, Email, OAuth, Logging) at **Admin → System → Settings** (`/admin/settings`). Sensitive values are masked. Changes must be made in `.env` (or environment) and the application restarted.

## Required Configuration

### Database Configuration

**PostgreSQL (Recommended):**
```env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=boilerplate_db
DB_USER=boilerplate_user
DB_PASSWORD=your_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

**SQLite (Development):**
```env
DB_TYPE=sqlite
DB_NAME=app.db
```

**PostgreSQL Superuser (for migrations):**
```env
POSTGRES_SUPERUSER=postgres
POSTGRES_SUPERUSER_PASSWORD=postgres_password
```

### Application Configuration

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Application Info
APP_NAME=Your Application Name
APP_VERSION=1.0.0
COMPANY_NAME=Your Company

# Security
JWT_SECRET_KEY=your-jwt-secret-key
```

### Email Configuration

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourapp.com
```

## Optional Configuration

### Cache Configuration

**Redis (Production):**
```env
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
```

**Simple Cache (Development):**
```env
CACHE_TYPE=simple
```

### Redis & Celery (optional)

Used for the admin monitoring health check, Celery task queue (email, session cleanup), and optional Redis cache.

**1. Start Redis locally**

**macOS (Homebrew):**
```bash
brew services start redis
# Or run in foreground: redis-server
```

**Ubuntu/Debian:**
```bash
sudo systemctl start redis-server
```

**2. Add to `.env` (optional; defaults are below):**
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

If Redis is not running, the app still works; admin monitoring will show Redis/Celery as "Unavailable" and Celery tasks will not run until Redis is started.

**Verify Redis is running:**
```bash
redis-cli ping
# Expect: PONG
```

### Celery setup (optional)

Celery runs background tasks (email queue, session cleanup, etc.) and uses Redis as the broker.

**1. Redis must be running** (see “Redis & Celery” above).

**2. Install Celery dependencies:**
```bash
pip install -r requirements/requirements-celery.txt
```

**3. Add to `.env` (optional; defaults already point to local Redis):**
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**4. Start the Celery worker** (in a separate terminal):
```bash
celery -A celery_app.celery worker --loglevel=info
```

**5. For periodic tasks** (session cleanup, etc.), start Beat in another terminal:
```bash
celery -A celery_app.celery beat --loglevel=info
```

**6. Optional – Flower (monitoring UI):**
```bash
pip install flower   # if not in requirements-celery.txt
celery -A celery_app.celery flower
```
Then open `http://localhost:5555`.

**Summary:** Run Redis first, then `celery -A celery_app.celery worker`. See `docs/03-development/email/EMAIL_QUEUE_CELERY.md` for usage and production setup.

### Logging Configuration

```env
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### File Upload Configuration

```env
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
```

## Configuration Variables Reference

### Database Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_TYPE` | Database type (postgresql, sqlite, mysql, mariadb, mssql) | `sqlite` | No |
| `DB_HOST` | Database host | `localhost` | PostgreSQL: Yes |
| `DB_PORT` | Database port | `5432` (PostgreSQL) | No |
| `DB_NAME` | Database name | `app.db` | Yes |
| `DB_USER` | Database username | - | PostgreSQL: Yes |
| `DB_PASSWORD` | Database password | - | PostgreSQL: Yes |
| `DB_POOL_SIZE` | Connection pool size | `10` | No |
| `DB_MAX_OVERFLOW` | Max pool overflow | `20` | No |
| `POSTGRES_SUPERUSER` | PostgreSQL superuser | `postgres` | No |
| `POSTGRES_SUPERUSER_PASSWORD` | Superuser password | - | No |

### Application Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key-change-in-production` | **Yes** (change in prod) |
| `FLASK_ENV` | Flask environment | `development` | No |
| `FLASK_DEBUG` | Debug mode | `True` | No |
| `APP_NAME` | Application name | `Core Application` | No |
| `APP_VERSION` | Application version | `1.0.0` | No |
| `COMPANY_NAME` | Company name | `Your Company` | No |

### Security Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JWT_SECRET_KEY` | JWT signing key | `jwt-secret-key-change-in-production` | **Yes** (change in prod) |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token expiration (seconds) | `3600` | No |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token expiration (seconds) | `2592000` | No |

### Email Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAIL_SERVER` | SMTP server | - | No |
| `MAIL_PORT` | SMTP port | `587` | No |
| `MAIL_USE_TLS` | Use TLS | `True` | No |
| `MAIL_USERNAME` | SMTP username | - | No |
| `MAIL_PASSWORD` | SMTP password | - | No |
| `MAIL_DEFAULT_SENDER` | Default sender | - | No |

### Cache Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL | - | No |
| `CACHE_TYPE` | Cache type (redis, simple) | `simple` | No |
| `CACHE_DEFAULT_TIMEOUT` | Cache timeout (seconds) | `300` | No |

## Generating Secret Keys

### Generate SECRET_KEY

```bash
python3 scripts/generate_secret_key.py
```

### Generate JWT_SECRET_KEY

```bash
python3 scripts/generate_secret_key.py
# Use different key for JWT
```

## Environment-Specific Configuration

### Development

```env
FLASK_ENV=development
FLASK_DEBUG=True
DB_TYPE=sqlite
CACHE_TYPE=simple
LOG_LEVEL=DEBUG
```

### Production

```env
FLASK_ENV=production
FLASK_DEBUG=False
DB_TYPE=postgresql
DB_HOST=your-db-host
DB_NAME=production_db
CACHE_TYPE=redis
REDIS_URL=redis://your-redis-host:6379/0
LOG_LEVEL=INFO
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
```

### Testing

```env
FLASK_ENV=testing
TESTING=True
DB_TYPE=sqlite
SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
WTF_CSRF_ENABLED=False
```

## Configuration Validation

The application validates configuration on startup:

```python
# Checks performed:
- Database connection
- Required environment variables
- Secret keys (warns if defaults)
- Email configuration (if provided)
```

**View validation results:**
- Check application logs on startup
- Use `/health` endpoint
- Run `flask config-validate`

## Security Best Practices

### 1. Never Commit Secrets

- `.env` should be in `.gitignore`
- Use `env.example` for documentation
- Use placeholders in example files

### 2. Use Strong Secret Keys

```bash
# Generate strong keys
python3 scripts/generate_secret_key.py
```

### 3. Rotate Keys Regularly

- Change `SECRET_KEY` periodically
- Change `JWT_SECRET_KEY` if compromised
- Update database passwords regularly

### 4. Use Environment Variables in Production

```bash
# Set in system environment (not files)
export SECRET_KEY="your-secret-key"
export DB_PASSWORD="your-db-password"
```

### 5. Restrict File Permissions

```bash
# Make .env readable only by owner
chmod 600 .env
```

## Database Configuration Details

### PostgreSQL Connection String

The application builds connection strings automatically:

```
postgresql://user:password@host:port/database
```

### Connection Pooling

```env
DB_POOL_SIZE=10          # Base pool size
DB_MAX_OVERFLOW=20       # Max overflow connections
DB_POOL_TIMEOUT=30       # Connection timeout (seconds)
```

### SSL Configuration

For PostgreSQL SSL connections, add to connection options:

```python
# In database_config.py or .env
DB_OPTIONS=sslmode=require
```

## Email Configuration Details

### Gmail Setup

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password  # Not regular password!
```

**Note:** Gmail requires an "App Password" for SMTP access.

### Other Providers

**SendGrid:**
```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

**AWS SES:**
```env
MAIL_SERVER=email-smtp.us-east-1.amazonaws.com
MAIL_PORT=587
MAIL_USERNAME=your-aws-access-key
MAIL_PASSWORD=your-aws-secret-key
```

## Cache Configuration

### Redis Setup

```env
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300
```

**Redis with Password:**
```env
REDIS_URL=redis://:password@localhost:6379/0
```

**Redis with SSL:**
```env
REDIS_URL=rediss://localhost:6380/0
```

### Simple Cache (Development)

```env
CACHE_TYPE=simple
```

Uses in-memory cache (not persistent, not shared across processes).

## Logging Configuration

### Log Levels

- `DEBUG` - Detailed information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### Log File Location

```env
LOG_FILE=logs/app.log
```

Logs are automatically rotated and archived.

## Configuration Testing

### Test Configuration

```bash
# Validate configuration
flask config-validate

# Test database connection
flask db-health

# Test email configuration
flask test-email
```

## Troubleshooting

### Configuration Not Loading

1. Check `.env` file exists in project root
2. Verify file permissions
3. Check for syntax errors (no spaces around `=`)
4. Restart application after changes

### Database Connection Fails

1. Verify database is running
2. Check credentials in `.env`
3. Test connection: `psql -U user -d database`
4. Check firewall/network settings

### Secret Key Warnings

If you see warnings about default secret keys:
1. Generate new keys: `python3 scripts/generate_secret_key.py`
2. Update `.env` file
3. Restart application

## Job Seeker Automation

Configuration for job discovery, LLM tailoring, browser scraping, and auto-apply. See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) for step-by-step setup.

### Discovery APIs

```env
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
DISCOVERY_RATE_LIMIT_PER_HOUR=100
```

### LLM Tailoring

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_API_KEY=          # Checked but not yet implemented
```

Without `OPENAI_API_KEY`, tailoring uses heuristic fallbacks (no configuration needed).

### Credential Encryption

Required for storing LinkedIn/Indeed portal sessions:

```env
# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
CREDENTIAL_ENCRYPTION_KEY=your-fernet-key
```

### Playwright Browser Automation

```env
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_CHANNEL=chrome          # Use system Chrome (recommended on macOS)
INDEED_PLAYWRIGHT_HEADLESS=false   # Indeed blocks headless browsers
```

### Scraping Flags (default: disabled)

```env
LINKEDIN_SCRAPE_ENABLED=false
INDEED_SCRAPE_ENABLED=false
SCRAPE_RATE_LIMIT_PER_HOUR=20
SCRAPE_DELAY_MIN_MS=2000
SCRAPE_DELAY_MAX_MS=6000
SCRAPE_USE_REDIS=false             # false | true | auto
```

### Auto-Apply Flags (default: disabled)

```env
APPLY_AUTOMATION_ENABLED=false
LINKEDIN_AUTO_APPLY_ENABLED=false
INDEED_AUTO_APPLY_ENABLED=false
DAILY_APPLY_CAP=25
```

### Celery (optional — Docker/production)

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Local dev with `python run.py` does not require Redis or Celery.

## See Also

- [GETTING_STARTED.md](../01-getting-started/GETTING_STARTED.md) - Initial setup
- [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) - Job seeker automation setup
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Administrator guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production configuration
