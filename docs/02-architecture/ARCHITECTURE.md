# Application Architecture

## Overview

This Flask application follows a modular, scalable architecture designed for enterprise applications. It uses PostgreSQL schemas for logical database organization and implements a comprehensive RBAC system.

## Core Principles

1. **Modular Design** - Features organized into independent modules
2. **Schema Separation** - Database tables grouped by functional domain
3. **RBAC Compliance** - Role-based access control throughout
4. **API-First** - RESTful API alongside web interface
5. **Scalability** - Designed to grow with your needs

## Architecture Layers

### 1. Presentation Layer

**Templates** (`app/templates/`)
- Base templates: `base.html` (main app with sidebar), `base_auth.html` (login/register), `base_misc.html` (error/misc pages)
- Component templates: Header, Sidebar, Flash messages
- Module-specific templates organized by feature (see [TEMPLATES_AND_UI.md](../03-development/TEMPLATES_AND_UI.md))

**Static Assets** (`app/static/`)
- CSS (Vuexy theme and vendor styles, `page-misc.css` for error pages)
- JavaScript (Vuexy/Bootstrap 5 components)
- Images and media files

**Frontend Framework:**
- **Vuexy Theme** - Bootstrap 5 admin dashboard theme (vertical menu template)
- **Bootstrap 5** - Components and utilities
- **Tabler Icons** - Icon library (icon-base ti)

### 2. Application Layer

**Blueprints** (`app/modules/`)
Each module is a Flask blueprint with:
- `routes.py` - Web routes (HTML responses)
- `api.py` - API routes (JSON responses)
- `__init__.py` - Blueprint registration

**Current Modules:**
- `auth` - Authentication (login, register, password reset)
- `users` - User management (profile, account settings, view user, roles & permissions)
- `admin` - Admin panel (dashboard, monitoring, roles/permissions, email logs/templates, settings view, system logs, reports, developer sitemap)
- `main` - Dashboard and index
- Additional modules (e.g. `accounts`) may be present; see `app/modules/` and `config/modules.py` for the active menu.

### 3. Business Logic Layer

**Services** (`app/services/`)
Business logic separated from routes (if implemented)

**Models** (`app/models/`)
Database models organized by schema:
- `auth.py` - User, Role, Group models
- Additional model modules as needed; see `app/models/` and migration schemas.

### 4. Data Layer

**Database Schemas:**
- `auth` - Authentication and RBAC (6 tables)
- `accounts` - Business accounts (5 tables)
- `contacts` - Contacts (4 tables)
- `documents` - Documents (5 tables)
- `organizations` - Organizations (3 tables)
- `tenants` - Multi-tenancy (4 tables)
- `settings` - Settings (5 tables)
- `public` - System tables (1 table)

**See [DATABASE_SCHEMAS.md](DATABASE_SCHEMAS.md) for complete schema documentation.**

## Application Factory Pattern

The application uses Flask's application factory pattern:

```python
# app/__init__.py
def create_app(config_name=None):
    app = Flask(__name__)
    
    # Initialize configuration
    init_config(app, config_name)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app
```

**Benefits:**
- Easy testing (create app instances for tests)
- Multiple app instances (different configs)
- Delayed initialization (extensions initialized after app creation)

## Extension System

**Core Extensions** (`app/extensions/`):
- `core.py` - Database, cache, login manager, etc.
- `config.py` - Configuration management
- `blueprints.py` - Blueprint registration
- `template_context.py` - Template context processors
- `error_handlers.py` - Error handling
- `database_config.py` - Multi-database support
- `database_health.py` - Database monitoring
- `database_backup.py` - Backup system

## Request Flow

```
1. HTTP Request
   ↓
2. Flask App (WSGI)
   ↓
3. Middleware (CSRF, Rate Limiting, CORS)
   ↓
4. Blueprint Router
   ↓
5. Route Handler (routes.py or api.py)
   ↓
6. Business Logic (if services exist)
   ↓
7. Database Models (app/models/)
   ↓
8. Database (PostgreSQL/SQLite)
   ↓
9. Response (HTML template or JSON)
```

## Authentication Flow

```
1. User submits login form
   ↓
2. Auth route validates credentials
   ↓
3. User model checks password hash
   ↓
4. Account lockout check
   ↓
5. Flask-Login creates session
   ↓
6. User redirected to dashboard
   ↓
7. Template context injects user info
```

## RBAC Flow

```
1. User makes request
   ↓
2. Route checks @login_required
   ↓
3. Permission check (if needed)
   ↓
4. User.has_permission('module.action')
   ↓
5. Check direct roles → Check group roles
   ↓
6. Permission granted/denied
   ↓
7. Route handler executes or returns 403
```

## Database Schema Organization

Tables are organized into PostgreSQL schemas:

```
auth/
  ├── users
  ├── roles
  ├── groups
  ├── user_roles
  ├── user_groups
  └── group_roles

accounts/
  ├── accounts
  ├── account_types
  ├── account_categories
  ├── account_activities
  └── account_settings

... (other schemas)
```

**Benefits:**
- Logical organization
- Schema-level permissions possible
- Easier backup/restore
- Better security isolation

## Module Structure

Each module follows this structure:

```
app/modules/module_name/
├── __init__.py          # Blueprint exports
├── routes.py            # Web routes
└── api.py               # API routes (optional)

app/templates/modules/module_name/
├── list.html            # List view
├── create.html          # Create form
├── edit.html            # Edit form
└── ...                  # Subfolders by feature (e.g. profile/, view/, settings/)
```

The **users** module uses subfolders: `profile/`, `view/`, `view/includes/`, `settings/`, `settings/includes/`, `access/`. See [TEMPLATES_AND_UI.md](../03-development/TEMPLATES_AND_UI.md). Development docs are in `03-development/` with subfolders: `admin/`, `auth/`, `rbac/`, `email/`.

## Configuration Management

**Environment Variables** (`.env`):
- Database configuration
- Secret keys
- Email settings
- Feature flags

**Configuration Loading:**
1. Load from `.env` file
2. Load from `.env.local` (if exists, overrides)
3. Load from system environment (overrides all)

**See [CONFIGURATION.md](CONFIGURATION.md) for details.**

## Security Features

1. **Password Hashing** - Bcrypt with salt
2. **CSRF Protection** - Flask-WTF CSRF tokens
3. **Account Lockout** - After 5 failed attempts (30 min)
4. **Password Reset** - Secure token-based
5. **Email Verification** - Token-based verification
6. **Session Management** - Flask-Login sessions
7. **Rate Limiting** - Flask-Limiter on API endpoints
8. **SQL Injection Protection** - SQLAlchemy ORM

## Scalability Considerations

1. **Database Connection Pooling** - Configured in `database_config.py`
2. **Caching** - Redis support (optional)
3. **Horizontal Scaling** - Stateless application design
4. **Schema Isolation** - Allows tenant-specific schemas if needed
5. **Module-based** - Easy to add/remove features

## Technology Stack

- **Backend:** Flask 3.x, Python 3.x
- **Database:** PostgreSQL 12+ (primary), SQLite (dev)
- **ORM:** SQLAlchemy 2.x
- **Frontend:** Vuexy (Bootstrap 5) admin theme
- **Authentication:** Flask-Login
- **API:** Flask-RESTX (optional)
- **Migrations:** Flask-Migrate (Alembic)
- **Testing:** Pytest

## Design Patterns Used

1. **Application Factory** - Flask app creation
2. **Blueprint Pattern** - Modular route organization
3. **Repository Pattern** - Database abstraction (via SQLAlchemy)
4. **MVC Pattern** - Models, Views (templates), Controllers (routes)
5. **Dependency Injection** - Extensions injected via app context
6. **Template Inheritance** - Base templates with blocks

## Performance Optimizations

1. **Database Indexing** - Indexes on frequently queried columns
2. **Query Optimization** - Eager loading for relationships
3. **Caching** - Redis for frequently accessed data
4. **Static File Serving** - Nginx/CDN in production
5. **Connection Pooling** - Database connection reuse

## Monitoring & Health Checks

- **Database Health** - `/health/database` endpoint
- **Application Health** - `/health` endpoint
- **Logging** - Structured logging to `logs/app.log`
- **Error Tracking** - Error handlers with logging

## Future Enhancements

Potential areas for expansion:
- GraphQL API (infrastructure exists)
- WebSocket support
- Background job processing (Celery)
- Full-text search (PostgreSQL FTS or Elasticsearch)
- File storage abstraction (S3, Azure Blob)
- Advanced caching strategies
- API versioning
- Microservices migration path
