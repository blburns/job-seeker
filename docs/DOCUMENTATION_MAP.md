# Documentation Map

## Visual Structure

```
docs/
├── 00-OVERVIEW.md                    ⭐ START HERE
├── README.md                         📚 Documentation index
├── QUICK_REFERENCE.md                ⚡ Commands and patterns
├── DOCUMENTATION_MAP.md              🗺️ This file
│
├── 01-getting-started/
│   ├── GETTING_STARTED.md            🚀 Installation and setup
│   └── FIRST_RUN_CHECKLIST.md        ✅ Post-install verification
│
├── 02-user-guide/                    👤 END USER GUIDES
│   ├── README.md                     User guide index
│   ├── CONCEPTS.md                   Key terms
│   ├── WORKFLOW.md                   End-to-end workflow
│   ├── MASTER_PROFILE.md             Resume management
│   ├── JOB_DISCOVERY.md              Finding jobs
│   ├── APPLICATIONS.md               Pipeline tracking
│   ├── TAILORING_AND_APPLY.md        Tailoring and apply review
│   ├── BATCH_AUTO_APPLY.md           Batch submission
│   └── ANALYTICS.md                  Metrics dashboard
│
├── 02-architecture/
│   ├── ARCHITECTURE.md               🏗️ System design
│   └── JOB_SEEKER_SERVICES.md        ⚙️ Service layer
│
├── 03-development/
│   ├── JOB_SEEKER_API.md             🌐 Job seeker REST API
│   ├── SCRAPING_AND_AUTOMATION.md    🤖 Playwright and connectors
│   ├── MODULE_DEVELOPMENT.md         🧩 Building modules
│   ├── API_DOCUMENTATION.md          🌐 General API framework
│   ├── TEMPLATES_AND_UI.md           🎨 Templates and sidebar
│   ├── admin/                        🧭 Admin panel (boilerplate)
│   ├── auth/                         🔑 Auth and security (boilerplate)
│   ├── rbac/                         🔐 Permissions (boilerplate)
│   └── email/                        📧 Email (boilerplate)
│
├── 04-operations/
│   ├── ADMIN_GUIDE.md                👨‍💼 Administrator guide
│   ├── AUTOMATION_SETUP.md           🤖 Automation configuration
│   ├── CONFIGURATION.md              ⚙️ Environment variables
│   ├── DEPLOYMENT.md                 🚀 Production deployment
│   ├── INFRASTRUCTURE.md             🏗️ Redis, Celery, Sentry
│   └── TROUBLESHOOTING.md            🔧 Problem solving
│
├── 05-reference/
│   ├── JOB_SEEKER_DATA_MODEL.md      🗄️ Jobs schema tables
│   ├── ATS_EXPORT_RULES.md           📄 Resume export rules
│   ├── DATABASE_SCHEMAS.md           🗄️ Full database structure
│   └── SCHEMA_MIGRATION.md           🔄 Migration guide
│
└── 06-planning/                      📋 Legacy boilerplate planning
    └── (CRM, phase docs — not active product docs)
```

## Reading Paths

### Job seeker (end user)
1. [WORKFLOW.md](02-user-guide/WORKFLOW.md) — Full process
2. [MASTER_PROFILE.md](02-user-guide/MASTER_PROFILE.md) — Resume setup
3. [JOB_DISCOVERY.md](02-user-guide/JOB_DISCOVERY.md) — Finding jobs
4. [TAILORING_AND_APPLY.md](02-user-guide/TAILORING_AND_APPLY.md) — Tailoring and submission

### New to the project?
1. [00-OVERVIEW.md](00-OVERVIEW.md) — Application overview
2. [GETTING_STARTED.md](01-getting-started/GETTING_STARTED.md) — Setup
3. [FIRST_RUN_CHECKLIST.md](01-getting-started/FIRST_RUN_CHECKLIST.md) — Verify install

### Administrator?
1. [ADMIN_GUIDE.md](04-operations/ADMIN_GUIDE.md) — User and system management
2. [AUTOMATION_SETUP.md](04-operations/AUTOMATION_SETUP.md) — Configure automation
3. [DEPLOYMENT.md](04-operations/DEPLOYMENT.md) — Production setup
4. [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md) — Fix issues

### Developer?
1. [ARCHITECTURE.md](02-architecture/ARCHITECTURE.md) — System design
2. [JOB_SEEKER_SERVICES.md](02-architecture/JOB_SEEKER_SERVICES.md) — Service layer
3. [JOB_SEEKER_API.md](03-development/JOB_SEEKER_API.md) — API endpoints
4. [SCRAPING_AND_AUTOMATION.md](03-development/SCRAPING_AND_AUTOMATION.md) — Browser automation

### Quick lookup?
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## Documentation by Topic

### Job Seeker Features
- [WORKFLOW.md](02-user-guide/WORKFLOW.md) — End-to-end process
- [CONCEPTS.md](02-user-guide/CONCEPTS.md) — Key terms
- [JOB_SEEKER_DATA_MODEL.md](05-reference/JOB_SEEKER_DATA_MODEL.md) — Data model
- [ATS_EXPORT_RULES.md](05-reference/ATS_EXPORT_RULES.md) — Export rules

### Automation
- [AUTOMATION_SETUP.md](04-operations/AUTOMATION_SETUP.md) — Setup guide
- [SCRAPING_AND_AUTOMATION.md](03-development/SCRAPING_AND_AUTOMATION.md) — Developer guide
- [BATCH_AUTO_APPLY.md](02-user-guide/BATCH_AUTO_APPLY.md) — User guide

### Security and Auth (boilerplate)
- [AUTHENTICATION.md](03-development/auth/AUTHENTICATION.md)
- [RBAC_GUIDE.md](03-development/rbac/RBAC_GUIDE.md)

### Operations
- [ADMIN_GUIDE.md](04-operations/ADMIN_GUIDE.md)
- [CONFIGURATION.md](04-operations/CONFIGURATION.md)
- [DEPLOYMENT.md](04-operations/DEPLOYMENT.md)
- [TROUBLESHOOTING.md](04-operations/TROUBLESHOOTING.md)

## Quick Links

- **Overview:** [00-OVERVIEW.md](00-OVERVIEW.md)
- **User Guide:** [02-user-guide/README.md](02-user-guide/README.md)
- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full Index:** [README.md](README.md)
