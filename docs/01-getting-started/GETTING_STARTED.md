# Getting Started Guide

## Overview

This is a comprehensive Flask boilerplate application with enterprise-grade features including:
- **RBAC (Role-Based Access Control)** - Complete user, role, and group management
- **Multi-tenancy Support** - Built-in tenant isolation
- **Schema-based Database Organization** - Logical separation of database tables
- **Metronic Theme Integration** - Modern, responsive UI
- **RESTful API** - Complete API infrastructure
- **Module-based Architecture** - Scalable, maintainable code structure

## Prerequisites

- Python 3.14+
- PostgreSQL 12+ (recommended) or SQLite (development)
- Git

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd boilerplate-python3-flask

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings
# At minimum, configure:
# - DB_TYPE (postgresql or sqlite)
# - DB_NAME, DB_USER, DB_PASSWORD (for PostgreSQL)
# - SECRET_KEY (generate a secure key)
# - POSTGRES_SUPERUSER_PASSWORD (for schema migrations)
```

**Generate a secure SECRET_KEY:**
```bash
python3 scripts/generate_secret_key.py
```

### 3. Database Setup

#### Option A: PostgreSQL (Recommended)

```bash
# Create database
createdb boilerplate_db

# Update .env with database credentials
# DB_TYPE=postgresql
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=boilerplate_db
# DB_USER=your_user
# DB_PASSWORD=your_password
```

#### Option B: SQLite (Development)

```bash
# SQLite is the default - no setup needed
# Just ensure DB_TYPE=sqlite in .env (or leave default)
```

### 4. Run Database Migrations

```bash
# Initialize database with schemas
python3 scripts/migrate_to_schemas.py --confirm --superuser postgres

# Or if you have POSTGRES_SUPERUSER_PASSWORD in .env:
python3 scripts/migrate_to_schemas.py --confirm

# Create tables (if using Flask-Migrate)
flask db upgrade
```

### 5. Create Initial Data

```bash
# Create default roles, groups, and users
python3 scripts/create_default_roles_groups.py
python3 scripts/create_user.py
```

### 6. Run the Application

```bash
# Development mode
python3 run.py

# Or using Flask CLI
flask run

# The application will be available at:
# http://localhost:5000
```

## First Login

1. Navigate to `http://localhost:5000`
2. Click "Sign Up" to create your first account
3. Or use the default admin user created by scripts:
   - Username: `admin` (or as configured in scripts)
   - Password: Check script output or reset password

## Project Structure

```
boilerplate-python3-flask/
├── app/
│   ├── __init__.py          # Application factory
│   ├── main/                # Main blueprint (home, dashboard)
│   ├── modules/             # Feature modules
│   │   ├── auth/            # Authentication
│   │   ├── users/           # User management
│   │   ├── accounts/        # Business accounts
│   │   └── ...
│   ├── models/              # Database models (organized by schema)
│   │   ├── auth.py          # Auth schema models
│   │   ├── accounts.py      # Accounts schema models
│   │   └── ...
│   ├── api/                 # REST API
│   ├── extensions/          # Flask extensions
│   ├── templates/           # Jinja2 templates
│   ├── static/              # Static files (CSS, JS, images)
│   └── utils/               # Utility functions
├── config/                  # Configuration files
├── docs/                     # Documentation
├── migrations/              # Database migrations
├── scripts/                  # Utility scripts
├── tests/                   # Test files
├── .env                     # Environment variables (not in git)
├── requirements.txt         # Python dependencies
└── run.py                   # Application entry point
```

## Common Tasks

### Create a New User

```bash
python3 scripts/create_user.py
```

### Backup Database

```bash
python3 scripts/backup_database.py
```

### Run Tests

```bash
# Run all tests
python3 scripts/run_tests.py

# Or using pytest
pytest
```

### Check Database Health

```bash
flask db-health
```

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture
- Read [RBAC_GUIDE.md](RBAC_GUIDE.md) for permission system
- Read [MODULE_DEVELOPMENT.md](MODULE_DEVELOPMENT.md) to create new modules
- Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API usage
- Read [SCHEMA_MIGRATION.md](SCHEMA_MIGRATION.md) for database schema info

## Troubleshooting

### Database Connection Issues

1. Verify PostgreSQL is running: `pg_isready`
2. Check `.env` file has correct credentials
3. Test connection: `psql -U your_user -d your_database`

### Permission Errors

If you get permission errors during schema migration:
1. Ensure `POSTGRES_SUPERUSER_PASSWORD` is set in `.env`
2. Or run manually: `python3 scripts/migrate_to_schemas.py --confirm --superuser postgres`

### Import Errors

1. Ensure virtual environment is activated
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check Python path includes project root

### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process or use a different port
export FLASK_RUN_PORT=5001
flask run
```

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review error logs in `logs/app.log`
3. Check database health: `flask db-health`
