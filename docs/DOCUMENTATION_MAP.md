# Documentation Map

## Visual Structure

```
docs/
├── 00-OVERVIEW.md                    ⭐ START HERE
├── README.md                         📚 Navigation Index
├── QUICK_REFERENCE.md                ⚡ Quick Commands
├── DOCUMENTATION_MAP.md              🗺️ This File
├── CONFIGURATION.md                  ⚙️ Config (see also 04-operations)
│
├── 01-getting-started/
│   └── GETTING_STARTED.md            🚀 Setup & Installation
│
├── 02-architecture/
│   └── ARCHITECTURE.md               🏗️ System Design
│
├── 03-development/
│   ├── admin/                        🧭 Admin panel
│   │   ├── ADMIN_NAVIGATION.md
│   │   ├── ADMIN_SIDEBAR_MENU.md
│   │   └── DEVELOPER_SITEMAP.md
│   ├── auth/                         🔑 Auth & security
│   │   ├── AUTHENTICATION.md
│   │   ├── SESSION_MANAGEMENT.md
│   │   ├── TWO_FACTOR_AUTH.md
│   │   └── OAUTH_INTEGRATION.md
│   ├── rbac/                         🔐 Permissions
│   │   ├── RBAC_GUIDE.md
│   │   ├── RBAC_QUICK_START.md
│   │   └── PERMISSION_SYSTEM.md
│   ├── email/                        📧 Email
│   │   ├── EMAIL_SERVICE_SETUP.md
│   │   └── EMAIL_QUEUE_CELERY.md
│   ├── MODULE_DEVELOPMENT.md         🧩 Building Modules
│   ├── TEMPLATES_AND_UI.md           🎨 Sidebar, Users Templates, Error Pages
│   ├── API_DOCUMENTATION.md          🌐 REST API Reference
│   └── PHASE_1_1_SETUP.md
│
├── 04-operations/
│   ├── CONFIGURATION.md              ⚙️ Configuration
│   ├── DEPLOYMENT.md                 🚀 Production Deployment
│   ├── INFRASTRUCTURE.md             🏗️ Phase 1.5 (backup, Redis, Celery, Sentry, indexes)
│   └── TROUBLESHOOTING.md            🔧 Problem Solving
│
├── 05-reference/
│   ├── DATABASE_SCHEMAS.md           🗄️ Database Structure
│   ├── DATABASE_STRUCTURE.md         📋 Database structure (legacy)
│   ├── RBAC_ONLY_STRUCTURE.md        📋 RBAC-only app structure
│   └── SCHEMA_MIGRATION.md           🔄 Migration Guide
│
└── 06-planning/
    ├── TEMPLATE_FIXES_STATUS.md      📋 Template/UI status
    ├── ECOMMERCE_CRM_ERP_ARCHITECTURE.md
    ├── IMPLEMENTATION_TODO.md
    └── PHASE_*.md
```

## Reading Paths

### 🆕 New to the Project?
1. [00-OVERVIEW.md](00-OVERVIEW.md) - Start here for overview
2. [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md) - Setup instructions
3. [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md) - Understand the system

### 👨‍💻 Developer Building Features?
1. [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md) - Create modules
2. [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md) - Understand permissions
3. [API_DOCUMENTATION.md](03-development/API_DOCUMENTATION.md) - Build APIs

### 🔧 System Administrator?
1. [DEPLOYMENT.md](04-operations/DEPLOYMENT.md) - Production setup
2. [CONFIGURATION.md](04-operations/CONFIGURATION.md) - Configure app
3. [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) - Fix issues

### 🗄️ Database Administrator?
1. [DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md) - Schema structure
2. [SCHEMA_MIGRATION.md](05-reference/SCHEMA_MIGRATION.md) - Migrations
3. [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) - DB issues

### 🔍 Quick Lookup?
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Commands and patterns

## Documentation by Topic

### Security & Authentication
- [AUTHENTICATION.md](03-development/auth/AUTHENTICATION.md) - Auth system
- [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md) - Permissions

### Development
- [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md) - Building features
- [TEMPLATES_AND_UI.md](03-development/TEMPLATES_AND_UI.md) - Sidebar menu, users templates, error pages
- [API_DOCUMENTATION.md](03-development/API_DOCUMENTATION.md) - API development
- [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md) - System design
- [ADMIN_NAVIGATION.md](03-development/admin/ADMIN_NAVIGATION.md) - Admin structure and routes
- [ADMIN_SIDEBAR_MENU.md](03-development/admin/ADMIN_SIDEBAR_MENU.md) - Admin sidebar menu
- [DEVELOPER_SITEMAP.md](03-development/admin/DEVELOPER_SITEMAP.md) - Developer sitemap (all routes)
- [EMAIL_SERVICE_SETUP.md](03-development/email/EMAIL_SERVICE_SETUP.md) - Email config and Admin Email Templates

### Operations
- [DEPLOYMENT.md](04-operations/DEPLOYMENT.md) - Production deployment
- [CONFIGURATION.md](04-operations/CONFIGURATION.md) - Configuration
- [INFRASTRUCTURE.md](04-operations/INFRASTRUCTURE.md) - Phase 1.5 (backup, Redis, Celery, Sentry, indexes)
- [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) - Problem solving

### Database
- [DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md) - Schema reference
- [SCHEMA_MIGRATION.md](05-reference/SCHEMA_MIGRATION.md) - Migrations

## Quick Links

- **Overview:** [00-OVERVIEW.md](00-OVERVIEW.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full Index:** [README.md](README.md)
