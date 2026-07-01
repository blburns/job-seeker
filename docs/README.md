# Documentation

Welcome to the comprehensive documentation for the Flask Boilerplate Application. This documentation is organized into logical sections to help you find what you need quickly.

## 📚 Documentation Index

### 🚀 [00-OVERVIEW.md](00-OVERVIEW.md)
**Start here!** High-level overview of the application, features, architecture, and quick start guide.

---

## 📖 Getting Started

**For:** New users, first-time setup

- **[GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md)**
  - Installation and setup
  - Database configuration
  - First login
  - Project structure
  - Common tasks

---

## 🏗️ Architecture & Design

**For:** Developers, architects, technical leads

- **[ARCHITECTURE.md](02-architecture/ARCHITECTURE.md)**
  - System architecture overview
  - Design patterns used
  - Technology stack
  - Request flow
  - Security features
  - Scalability considerations

---

## 💻 Development Guides

**For:** Developers building features

### Core Concepts
- **[RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md)**
  - Role-Based Access Control system
  - Permission structure
  - Creating roles and groups
  - Permission checking in code
  - Best practices

- **[AUTHENTICATION.md](03-development/auth/AUTHENTICATION.md)**
  - Authentication flow
  - Security features
  - Password management
  - Session handling
  - Email verification
  - Password reset

### Building Features
- **[MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md)**
  - Creating new modules
  - Module structure
  - Step-by-step guide
  - Best practices
  - Common patterns

- **[TEMPLATES_AND_UI.md](03-development/TEMPLATES_AND_UI.md)**
  - Base templates (base.html, base_misc.html)
  - Sidebar menu (config/modules.py)
  - Users template organization (profile/, view/, settings/, access/)
  - Error pages (Vuexy misc layout)

- **[API_DOCUMENTATION.md](03-development/API_DOCUMENTATION.md)**
  - REST API reference
  - Authentication methods
  - Endpoint documentation
  - Request/response formats
  - Code examples

---

## ⚙️ Operations & Administration

**For:** System administrators, DevOps

- **[CONFIGURATION.md](04-operations/CONFIGURATION.md)**
  - Environment variables
  - Configuration management
  - Database configuration
  - Email setup
  - Cache configuration
  - Security settings

- **[DEPLOYMENT.md](04-operations/DEPLOYMENT.md)**
  - Production deployment
  - Server setup
  - Nginx configuration
  - SSL certificates
  - Process management
  - Monitoring
  - Backup procedures

- **[TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md)**
  - Common issues and solutions
  - Database problems
  - Authentication issues
  - Performance problems
  - Configuration errors
  - Debugging tips

---

## 📖 Reference Documentation

**For:** Quick lookups, detailed specifications

- **[DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md)**
  - Complete database structure
  - All tables and columns
  - Relationships
  - Schema organization
  - Field descriptions

- **[SCHEMA_MIGRATION.md](05-reference/SCHEMA_MIGRATION.md)**
  - Schema migration procedures
  - Moving tables to schemas
  - Permission management
  - Rollback procedures
  - Troubleshooting migrations

---

## Quick Navigation

### I want to...

**...get started quickly**
→ [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md)

**...understand the system**
→ [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md)

**...create a new feature**
→ [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md)

**...set up permissions**
→ [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md)

**...deploy to production**
→ [DEPLOYMENT.md](04-operations/DEPLOYMENT.md)

**...configure the application**
→ [CONFIGURATION.md](04-operations/CONFIGURATION.md)

**...fix a problem**
→ [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md)

**...understand the database**
→ [DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md)

**...use the API**
→ [API_DOCUMENTATION.md](03-development/API_DOCUMENTATION.md)

---

## Documentation by Role

### 👤 New User / Developer
1. [00-OVERVIEW.md](00-OVERVIEW.md) - Start here
2. [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md) - Setup
3. [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md) - Understand system
4. [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md) - Learn permissions
5. [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md) - Build features

### 🏗️ Architect / Technical Lead
1. [00-OVERVIEW.md](00-OVERVIEW.md) - Overview
2. [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md) - System design
3. [DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md) - Data model
4. [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md) - Security model

### 🔧 System Administrator
1. [DEPLOYMENT.md](04-operations/DEPLOYMENT.md) - Production setup
2. [CONFIGURATION.md](04-operations/CONFIGURATION.md) - Configuration
3. [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) - Problem solving
4. [SCHEMA_MIGRATION.md](05-reference/SCHEMA_MIGRATION.md) - Database migrations

### 🗄️ Database Administrator
1. [DATABASE_SCHEMAS.md](05-reference/DATABASE_SCHEMAS.md) - Schema structure
2. [SCHEMA_MIGRATION.md](05-reference/SCHEMA_MIGRATION.md) - Migration procedures
3. [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) - Database issues

### 🔌 API Developer
1. [API_DOCUMENTATION.md](03-development/API_DOCUMENTATION.md) - API reference
2. [AUTHENTICATION.md](03-development/auth/AUTHENTICATION.md) - Auth system
3. [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md) - Permissions

---

## Documentation Statistics

- **Total Documents:** 12
- **Total Size:** ~112KB
- **Sections:** 5 organized categories
- **Code Examples:** Included throughout
- **Cross-References:** Linked between documents

---

## Contributing to Documentation

When adding features or making changes:

1. Update relevant documentation files
2. Add code examples
3. Include troubleshooting tips
4. Update this README if adding new docs
5. Keep cross-references current

---

## Need Help?

1. **Quick Answer:** Check [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md)
2. **Setup Help:** See [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md)
3. **Architecture Questions:** Read [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md)
4. **Development Help:** Review [MODULE_DEVELOPMENT.md](03-development/MODULE_DEVELOPMENT.md)

---

**Docs structure:** Development guides are grouped under `03-development/` in subfolders: `admin/`, `auth/`, `rbac/`, `email/`. Reference docs (database, RBAC structure) are in `05-reference/`. Planning and status docs are in `06-planning/`.

---

**Last Updated:** 2026-01-31  
**Application Version:** 0.2.0
