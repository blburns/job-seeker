# Application Overview

## What is This?

This is a **production-ready Flask boilerplate application** designed as the foundation for building scalable, enterprise-grade web applications. It provides a complete RBAC-compliant authentication system, modular architecture, and comprehensive infrastructure for rapid application development.

## Key Features

### 🔐 Enterprise Security
- **RBAC System** - Complete role-based access control with users, roles, and groups
- **Multi-factor Authentication Ready** - Infrastructure for MFA implementation
- **Account Security** - Lockout protection, password strength validation, secure password reset
- **Session Management** - Secure session handling with Flask-Login
- **CSRF Protection** - Built-in CSRF token validation

### 🗄️ Database Architecture
- **Schema-based Organization** - Tables organized into logical PostgreSQL schemas
- **Multi-Database Support** - PostgreSQL (production), SQLite (development), MySQL, MS SQL Server
- **Migration System** - Comprehensive Alembic-based migrations
- **Health Monitoring** - Database connection and performance monitoring
- **Automated Backups** - Database backup and recovery system

### 🏗️ Scalable Architecture
- **Modular Design** - Blueprint-based module system
- **API-First** - RESTful API alongside web interface
- **Service Layer** - Business logic abstraction
- **Extension System** - Pluggable extensions for features
- **Multi-tenancy Ready** - Built-in tenant support

### 🎨 Modern Frontend
- **Vuexy Theme** - Bootstrap 5 admin dashboard theme (vertical menu)
- **Responsive Design** - Mobile-first approach
- **Component Library** - Reusable UI components (cards, tables, nav pills, modals)

### 🚀 Production Ready
- **Health Checks** - Application and database health endpoints
- **Logging** - Structured logging (e.g. `app/data/logs/`)
- **Error Handling** - Comprehensive error handling
- **Rate Limiting** - API rate limiting
- **Caching** - Redis support for performance
- **Admin Panel** - Settings (read-only config), system log viewer, reports, email templates (list, create, edit, preview), developer sitemap

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  Vuexy (Bootstrap 5) │ Jinja2 Templates        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  Flask Blueprints │ Routes │ API Endpoints               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Business Logic Layer                    │
│  Services │ Models │ Permission Checks                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                           │
│  PostgreSQL Schemas │ SQLAlchemy ORM │ Migrations        │
└─────────────────────────────────────────────────────────┘
```

## Database Schema Organization

```
auth/          → Authentication & RBAC (users, roles, groups)
accounts/      → Business account management
contacts/      → Contact management
documents/     → Document/file management
organizations/ → Organization & brand management
tenants/       → Multi-tenancy support
settings/      → Application settings
public/        → System tables
```

## Technology Stack

- **Backend:** Flask 3.x, Python 3.14+
- **Database:** PostgreSQL 12+ (primary), SQLite (dev)
- **ORM:** SQLAlchemy 2.x
- **Frontend:** Metronic Theme, KeenIcons
- **Authentication:** Flask-Login, JWT
- **API:** Flask-RESTX
- **Migrations:** Flask-Migrate (Alembic)
- **Caching:** Redis (optional)
- **Testing:** Pytest

## Quick Start

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Database**
   ```bash
   cp env.example .env
   # Edit .env with your database settings
   ```

3. **Initialize Database**
   ```bash
   python3 scripts/migrate_to_schemas.py --confirm
   flask db upgrade
   python3 scripts/create_default_roles_groups.py
   ```

4. **Run Application**
   ```bash
   python3 run.py
   ```

See [01-getting-started/GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md) for detailed instructions.

## Documentation Structure

### 📚 Getting Started
- **GETTING_STARTED.md** - Setup, installation, first steps

### 🏗️ Architecture
- **ARCHITECTURE.md** - System design, patterns, technology stack

### 💻 Development
- **RBAC_GUIDE.md** - Permission system and access control
- **MODULE_DEVELOPMENT.md** - Creating new modules
- **API_DOCUMENTATION.md** - REST API reference
- **AUTHENTICATION.md** - Auth system details

### ⚙️ Operations
- **CONFIGURATION.md** - Configuration management
- **DEPLOYMENT.md** - Production deployment
- **TROUBLESHOOTING.md** - Common issues and solutions

### 📖 Reference
- **DATABASE_SCHEMAS.md** - Complete database structure
- **SCHEMA_MIGRATION.md** - Database migration procedures

## Use Cases

### Building a New Application

1. Start with this boilerplate
2. Configure database and environment
3. Create your custom modules
4. Customize UI/UX
5. Deploy to production

### Adding Features

1. Create new module following patterns
2. Add database models
3. Create routes and API endpoints
4. Build templates
5. Configure permissions

### Multi-Tenant Applications

1. Use built-in tenant system
2. Configure tenant isolation
3. Set up tenant-specific settings
4. Deploy with tenant management

## Key Concepts

### RBAC (Role-Based Access Control)

Users → Roles → Permissions
Users → Groups → Roles → Permissions

**Permission Format:** `module.action`
- Example: `users.create`, `accounts.view`

### Module System

Each module is self-contained:
- Routes (web interface)
- API endpoints (REST API)
- Templates (UI)
- Models (database)

### Schema Organization

Database tables organized by functional domain:
- Logical separation
- Schema-level permissions possible
- Easier maintenance
- Better security

## Best Practices

1. **Always check permissions** before allowing actions
2. **Use schema-qualified names** for foreign keys
3. **Follow module structure** for consistency
4. **Test migrations** before production
5. **Use environment variables** for configuration
6. **Enable caching** in production
7. **Monitor health** endpoints
8. **Regular backups** of database

## Support & Resources

- **Documentation:** See `docs/` directory
- **Logs:** Check `app/data/logs/` (e.g. `app.log`, `error.log`, `security.log`, `audit.log`); admin log viewer at `/admin/logs`
- **Health:** `/health` endpoint
- **Database Health:** `/health/database` endpoint

## Next Steps

1. Read [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md)
2. Review [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md)
3. Explore [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md)
4. Start building with [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md)

---

**Version:** 0.2.0 | **Phase:** Core Services & Infrastructure | **Status:** ✅ Production Ready
