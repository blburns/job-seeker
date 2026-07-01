# Quick Reference Guide

## Common Commands

### Application

```bash
# Run development server
python3 run.py
# or
flask run

# Run with specific port
FLASK_RUN_PORT=5001 flask run
```

### Database

```bash
# Run migrations
flask db upgrade

# Create migration
flask db migrate -m "Description"

# Rollback migration
flask db downgrade

# Schema migration
python3 scripts/migrate_to_schemas.py --dry-run
python3 scripts/migrate_to_schemas.py --confirm

# Database health check
flask db-health
```

### User Management

```bash
# Create user
python3 scripts/create_user.py

# Create default roles/groups
python3 scripts/create_default_roles_groups.py

# Manage permissions
python3 scripts/manage_permissions.py --show
```

### Utilities

```bash
# Generate secret key
python3 scripts/generate_secret_key.py

# Backup database
python3 scripts/backup_database.py

# Run tests
pytest
# or
python3 scripts/run_tests.py
```

## Common Code Patterns

### Permission Check

```python
from flask_login import login_required, current_user

@route('/create')
@login_required
def create():
    if not current_user.has_permission('module.create'):
        flash('Permission denied', 'danger')
        return redirect(url_for('module.dashboard'))
    # Proceed
```

### Database Query

```python
from app.models.auth import User
from app.models.accounts import Account

# Query with schema
users = User.query.all()  # Queries auth.users
accounts = Account.query.all()  # Queries accounts.accounts

# Filter
user = User.query.filter_by(username='john').first()
active_accounts = Account.query.filter_by(status='active').all()
```

### Create Record

```python
from app.models.accounts import Account
from app.extensions.core import db

account = Account(
    account_name='New Company',
    status='active'
)
db.session.add(account)
db.session.commit()
```

### Update Record

```python
account = Account.query.get(account_id)
account.account_name = 'Updated Name'
account.updated_at = datetime.utcnow()
db.session.commit()
```

### Delete Record (Soft Delete)

```python
account = Account.query.get(account_id)
account.soft_delete()  # Sets is_deleted=True
db.session.commit()
```

## Environment Variables Quick Reference

```env
# Required
SECRET_KEY=<generate-with-script>
DB_TYPE=postgresql
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

# Optional but Recommended
POSTGRES_SUPERUSER_PASSWORD=postgres_password
JWT_SECRET_KEY=<generate-with-script>
MAIL_SERVER=smtp.gmail.com
REDIS_URL=redis://localhost:6379/0
```

## URL Patterns

### Web Routes

```
/auth/login              → Login page
/auth/register           → Registration
/                        → Dashboard (main index)
/users/list              → List users
/users/create            → Create user
/users/profile           → Current user profile
/users/profile/edit      → Edit profile
/users/profile/teams    → Profile teams
/users/settings          → Redirects to /users/settings/account
/users/settings/account  → Account settings (Account tab)
/users/settings/security → Account settings (Security tab)
/users/settings/billing  → Account settings (Billing tab)
/users/settings/notifications → Account settings (Notifications tab)
/users/settings/connections  → Account settings (Connections tab)
/users/view/<user_id>    → View user (Account tab)
/users/view/<user_id>/security → View user Security tab
/users/roles-permissions → Roles list
/users/permissions      → Permissions list
```

### Admin Routes (admin.access or equivalent)

```
/admin, /admin/dashboard     → Admin dashboard
/admin/monitoring            → System monitoring
/admin/permissions           → List permissions
/admin/permissions/create    → Create permission
/admin/permissions/<id>/edit → Edit permission
/admin/roles                → List roles
/admin/roles/create         → Create role
/admin/roles/<id>           → View role
/admin/roles/<id>/edit      → Edit role
/admin/roles/<id>/permissions → Manage role permissions
/admin/email/logs           → Email logs
/admin/email/templates      → List email templates
/admin/email/templates/create → Create template
/admin/email/templates/<name>/preview → Preview template (sample context)
/admin/email/templates/<name>/edit    → Edit template
/admin/settings             → Read-only config (from env)
/admin/logs                 → System log viewer
/admin/reports              → Aggregated reports
/admin/developer/sitemap     → All routes by blueprint
```

### API Routes

```
POST   /api/v1/auth/login      → Authenticate
GET    /api/v1/users           → List users
POST   /api/v1/users           → Create user
GET    /api/v1/users/<id>      → Get user
PUT    /api/v1/users/<id>      → Update user
DELETE /api/v1/users/<id>      → Delete user
```

## Permission Format

```
{module}.{action}

Examples:
- users.view
- users.create
- accounts.update
- documents.delete
```

## Schema Reference

```
auth.users          → User accounts
auth.roles          → RBAC roles
auth.groups         → User groups
accounts.accounts   → Business accounts
contacts.contacts   → Contacts
documents.documents → Documents
```

## Template Blocks

**Main app (base.html):**
```jinja2
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}
{% block content %}
  <!-- Page content -->
{% endblock %}
{% block extra_css %}{% endblock %}
{% block extra_js %}{% endblock %}
```

**Error / misc pages (base_misc.html):**  
Blocks: `title`, `misc_code`, `misc_heading`, `misc_description`, `misc_actions`, `misc_image`.  
See [TEMPLATES_AND_UI.md](03-development/TEMPLATES_AND_UI.md). Development docs are grouped under `03-development/` (admin/, auth/, rbac/, email/).

## Common Imports

```python
# Flask
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user

# Models
from app.models.auth import User, Role, Group
from app.models.accounts import Account

# Database
from app.extensions.core import db

# Utilities
from app.utils.security import validate_password_strength, sanitize_input
```

## File Locations

```
Configuration:     .env
Logs:             app/data/logs/ (access.log, app.log, error.log, security.log, audit.log)
Static Files:     app/static/
Templates:        app/templates/
Email Templates:  app/templates/emails/
Models:           app/models/
Routes:           app/modules/*/routes.py
API:              app/modules/*/api.py
Scripts:          scripts/
Migrations:       migrations/
```

## Health Check Endpoints

```
GET /health              → Application health
GET /health/database      → Database health
GET /api/v1/health       → API health
```

## See Full Documentation

- [00-OVERVIEW.md](00-OVERVIEW.md) - Complete overview
- [README.md](README.md) - Documentation index
- Individual guides in subdirectories
