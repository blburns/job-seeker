# Documentation

Comprehensive documentation for the Job Seeker Automation App.

## Start Here

| Audience | First read |
|----------|------------|
| **Job seeker** | [User Guide](02-user-guide/README.md) → [Workflow](02-user-guide/WORKFLOW.md) |
| **New install** | [Getting Started](01-getting-started/GETTING_STARTED.md) |
| **Administrator** | [Admin Guide](04-operations/ADMIN_GUIDE.md) |
| **Developer** | [Architecture](02-architecture/ARCHITECTURE.md) |
| **Overview** | [00-OVERVIEW.md](00-OVERVIEW.md) |

---

## User Guide

**For:** Job seekers using the application

| Doc | Description |
|-----|-------------|
| [README](02-user-guide/README.md) | User guide index |
| [CONCEPTS](02-user-guide/CONCEPTS.md) | Key terms and concepts |
| [WORKFLOW](02-user-guide/WORKFLOW.md) | End-to-end workflow |
| [MASTER_PROFILE](02-user-guide/MASTER_PROFILE.md) | Resume upload and management |
| [JOB_DISCOVERY](02-user-guide/JOB_DISCOVERY.md) | Finding jobs |
| [APPLICATIONS](02-user-guide/APPLICATIONS.md) | Pipeline and tracking |
| [TAILORING_AND_APPLY](02-user-guide/TAILORING_AND_APPLY.md) | Tailoring and apply review |
| [BATCH_AUTO_APPLY](02-user-guide/BATCH_AUTO_APPLY.md) | Batch submission |
| [ANALYTICS](02-user-guide/ANALYTICS.md) | Metrics dashboard |

---

## Getting Started

**For:** First-time setup

| Doc | Description |
|-----|-------------|
| [GETTING_STARTED](01-getting-started/GETTING_STARTED.md) | Installation and setup |
| [FIRST_RUN_CHECKLIST](01-getting-started/FIRST_RUN_CHECKLIST.md) | Post-install verification |

---

## Architecture

**For:** Developers and technical leads

| Doc | Description |
|-----|-------------|
| [ARCHITECTURE](02-architecture/ARCHITECTURE.md) | System architecture |
| [JOB_SEEKER_SERVICES](02-architecture/JOB_SEEKER_SERVICES.md) | Service layer reference |

---

## Development

**For:** Developers building features

| Doc | Description |
|-----|-------------|
| [JOB_SEEKER_API](03-development/JOB_SEEKER_API.md) | REST API reference |
| [SCRAPING_AND_AUTOMATION](03-development/SCRAPING_AND_AUTOMATION.md) | Playwright, connectors, adapters |
| [MODULE_DEVELOPMENT](03-development/MODULE_DEVELOPMENT.md) | Creating new modules |
| [API_DOCUMENTATION](03-development/API_DOCUMENTATION.md) | General API framework |
| [TEMPLATES_AND_UI](03-development/TEMPLATES_AND_UI.md) | Templates and sidebar |
| [RBAC_GUIDE](03-development/rbac/RBAC_GUIDE.md) | Permission system |
| [AUTHENTICATION](03-development/auth/AUTHENTICATION.md) | Auth system |

---

## Operations

**For:** Administrators and DevOps

| Doc | Description |
|-----|-------------|
| [ADMIN_GUIDE](04-operations/ADMIN_GUIDE.md) | User management, monitoring |
| [AUTOMATION_SETUP](04-operations/AUTOMATION_SETUP.md) | Scraping, LLM, auto-apply |
| [CONFIGURATION](04-operations/CONFIGURATION.md) | Environment variables |
| [DEPLOYMENT](04-operations/DEPLOYMENT.md) | Production deployment |
| [TROUBLESHOOTING](04-operations/TROUBLESHOOTING.md) | Problem solving |

---

## Reference

**For:** Quick lookups

| Doc | Description |
|-----|-------------|
| [JOB_SEEKER_DATA_MODEL](05-reference/JOB_SEEKER_DATA_MODEL.md) | Database tables and relationships |
| [ATS_EXPORT_RULES](05-reference/ATS_EXPORT_RULES.md) | Resume export constraints |
| [DATABASE_SCHEMAS](05-reference/DATABASE_SCHEMAS.md) | Full database structure |
| [QUICK_REFERENCE](QUICK_REFERENCE.md) | Commands and patterns |

---

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Use the app as a job seeker | [User Guide](02-user-guide/README.md) |
| Install the application | [Getting Started](01-getting-started/GETTING_STARTED.md) |
| Configure automation | [Automation Setup](04-operations/AUTOMATION_SETUP.md) |
| Understand the architecture | [Architecture](02-architecture/ARCHITECTURE.md) |
| Use the API | [Job Seeker API](03-development/JOB_SEEKER_API.md) |
| Deploy to production | [Deployment](04-operations/DEPLOYMENT.md) |
| Fix a problem | [Troubleshooting](04-operations/TROUBLESHOOTING.md) |
| Look up a command | [Quick Reference](QUICK_REFERENCE.md) |
| Plan toward production | [ROADMAP.md](../ROADMAP.md) |

---

## Documentation by Role

### Job Seeker
1. [Workflow](02-user-guide/WORKFLOW.md)
2. [Master Profile](02-user-guide/MASTER_PROFILE.md)
3. [Job Discovery](02-user-guide/JOB_DISCOVERY.md)
4. [Tailoring and Apply](02-user-guide/TAILORING_AND_APPLY.md)

### Administrator
1. [Admin Guide](04-operations/ADMIN_GUIDE.md)
2. [Automation Setup](04-operations/AUTOMATION_SETUP.md)
3. [Configuration](04-operations/CONFIGURATION.md)
4. [Deployment](04-operations/DEPLOYMENT.md)

### Developer
1. [Architecture](02-architecture/ARCHITECTURE.md)
2. [Job Seeker Services](02-architecture/JOB_SEEKER_SERVICES.md)
3. [Job Seeker API](03-development/JOB_SEEKER_API.md)
4. [Scraping and Automation](03-development/SCRAPING_AND_AUTOMATION.md)

---

## Legacy Boilerplate Docs

The following docs describe the inherited CRM boilerplate foundation. They remain available for RBAC, auth, and admin panel reference but are not specific to the job seeker product:

- `03-development/rbac/` — RBAC system
- `03-development/auth/` — Authentication, 2FA, OAuth
- `03-development/admin/` — Admin panel navigation
- `03-development/email/` — Email service
- `06-planning/CRM_*` — Legacy CRM planning docs

---

**Last Updated:** 2026-07-06
**Application Version:** 0.2.0
