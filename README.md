# Flask Application Boilerplate

## Overview
A modern, enterprise-grade Flask application boilerplate designed to serve as the foundation for 40+ business applications in the Dreamlike ecosystem. Built with security, scalability, and maintainability as core principles.

## 🚀 Current Status: v0.2.0 - Phase 2 Complete
**Version:** `0.2.0` | **Phase:** Core Services & Infrastructure | **Status:** ✅ **COMPLETED**

- ✅ Application Architecture Setup
- ✅ Database Architecture  
- ✅ Authentication & Authorization System
- ✅ API Infrastructure
- ✅ Communication Services
- ✅ Caching & Performance

## Features

### 🔐 **Security & Authentication**
- **JWT Token Management** - Secure token validation and refresh
- **Multi-Device Session Management** - Track and manage user sessions across devices
- **Role-Based Access Control (RBAC)** - Comprehensive user, role, and group management
- **Advanced Security Features** - Account lockout, brute force protection, password strength validation
- **Security Event Logging** - Comprehensive security monitoring and audit trails
- **Python3 Identity Manager Integration** - External identity provider support

### 🗄️ **Database Architecture**
- **Multi-Database Support** - SQLite, PostgreSQL, MySQL/MariaDB, MS SQL Server
- **Database Health Monitoring** - Connection testing, performance metrics, and diagnostics
- **Automated Backup & Recovery** - Comprehensive backup system with CLI tools
- **Migration Testing Framework** - Safe migration testing and validation
- **Connection Pooling** - Optimized database connections with retry logic

### 🏗️ **Application Architecture**
- **Modular Blueprint System** - Clean separation of concerns
- **Service Layer Architecture** - Business logic abstraction
- **Secret Management** - Encrypted storage for sensitive configuration
- **Configuration Validation** - Multi-environment configuration with validation
- **Development Tools** - Pre-commit hooks, code formatting, linting, type checking

### 🎨 **Frontend & UI**
- **Tailwind CSS Vanilla** - Utility-first CSS framework
- **Modern Responsive Design** - Mobile-first approach
- **Component-Based Templates** - Reusable UI components
- **Alpine.js Integration** - Lightweight JavaScript framework

### 🌐 **API Infrastructure**
- **RESTful API Framework** - Flask-RESTX with comprehensive endpoints
- **API Versioning** - Structured v1 API with future version support
- **Request/Response Middleware** - Authentication, rate limiting, CORS
- **API Documentation** - Swagger/OpenAPI documentation with Swagger UI
- **Rate Limiting** - Configurable rate limits per endpoint
- **CORS Support** - Cross-origin resource sharing configuration
- **API Health Checks** - Comprehensive health monitoring endpoints

### 📧 **Communication Services**
- **Enhanced Email Service** - Template-based email with multiple providers
- **Notification System** - Multi-channel notification delivery
- **Template Engine** - Dynamic content rendering for messages
- **Bulk Messaging** - Efficient bulk notification delivery
- **Delivery Tracking** - Message status and delivery confirmation
- **Channel Support** - Email, SMS, Push, In-App, Webhook channels

### ⚡ **Caching & Performance**
- **Redis Integration** - High-performance caching with Redis
- **Caching Strategies** - Advanced caching patterns and decorators
- **Performance Monitoring** - Cache health checks and statistics
- **Memoization Support** - Function result caching
- **Cache Management** - Key generation, expiration, and cleanup
- **Fallback Caching** - Simple cache fallback for development

### 🧪 **Testing & Quality**
- **Comprehensive Testing Suite** - Unit, integration, and API testing
- **Code Quality Tools** - Black, isort, flake8, pylint, mypy
- **Test Coverage** - Automated coverage reporting
- **Migration Testing** - Safe database migration testing

## Improvements Over dreamlikelabs-site
- **Cleaner Architecture** - Simplified extension management
- **Modern Dependencies** - Updated to latest stable versions
- **Better Testing** - Comprehensive test coverage
- **API-First Design** - REST and GraphQL APIs
- **Modern Frontend** - Tailwind CSS vanilla (no Flowbite dependency)
- **Better Documentation** - Comprehensive docs and examples
- **Type Hints** - Full type annotation support
- **Security** - Enhanced security practices

## Technology Stack

### **Backend & Core**
- **Flask 2.3+** - Web framework
- **Python 3.9+** - Programming language
- **SQLAlchemy 2.0+** - ORM and database toolkit
- **Alembic** - Database migration tool
- **Flask-Login** - User session management
- **Flask-JWT-Extended** - JWT token handling

### **Database Support**
- **PostgreSQL 14+** - Primary production database
- **SQLite** - Development and testing
- **MySQL/MariaDB** - Alternative production option
- **MS SQL Server** - Enterprise database support
- **Redis** - Caching and session storage

### **Frontend & UI**
- **Tailwind CSS 3.3+** - Utility-first CSS framework
- **Alpine.js 3.0+** - Lightweight JavaScript framework
- **Jinja2** - Template engine

### **Security & Authentication**
- **JWT Tokens** - Secure authentication
- **Bcrypt** - Password hashing
- **Cryptography** - Secret management
- **Flask-CORS** - Cross-origin resource sharing
- **Flask-Limiter** - Rate limiting

### **Development & Testing**
- **pytest** - Testing framework
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **pre-commit** - Git hooks

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- Node.js 18+ (for Tailwind CSS)
- Git

### Installation
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install  # For Tailwind CSS
   ```
4. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. Initialize database:
   ```bash
   flask db upgrade
   flask seed  # Optional: seed with sample data
   ```
   
   **Note**: The database is automatically seeded with default users, roles, and groups during migration. See [Default Users](#default-users) section below for login credentials.
6. Build frontend assets:
   ```bash
   npm run build
   ```
7. Start development server:
   ```bash
   flask run
   ```

## Default Users

The boilerplate comes with pre-configured users for testing and development. These users are automatically created when you run `flask db upgrade`.

### 🔐 **Default User Accounts**

| Username | Email | Password | Role | Group | Admin | SuperAdmin |
|----------|-------|----------|------|-------|-------|------------|
| `superadmin` | `superadmin@dreamlike.com` | `SuperAdmin123!` | superadmin | superadmins | ✅ | ✅ |
| `admin` | `admin@dreamlike.com` | `Admin123!` | admin | admins | ✅ | ❌ |
| `manager` | `manager@dreamlike.com` | `Manager123!` | manager | managers | ❌ | ❌ |
| `user` | `user@dreamlike.com` | `User123!` | user | users | ❌ | ❌ |

### 🛡️ **Role Permissions**

- **superadmin**: Full system access with all permissions (`*`)
- **admin**: Administrative access to most system features
- **manager**: Management access to users and basic system features
- **user**: Standard user access to basic features
- **guest**: Limited access for guest users

### 🔒 **Security Notes**

- All passwords are securely hashed using Werkzeug's password hashing
- All users have verified email addresses
- Users are assigned appropriate roles and groups automatically
- **Important**: Change default passwords in production environments

### 🚀 **Quick Login**

You can immediately log in to the application using any of the above credentials:

```bash
# Start the development server
flask run

# Then visit: http://localhost:5000/login
# Use any of the credentials above
   ```

## Project Structure
```
boilerplate/
├── app/
│   ├── __init__.py              # Application factory
│   ├── extensions/              # Flask extensions and configuration
│   │   ├── core.py              # Core extensions (db, cache, etc.)
│   │   ├── config.py            # Configuration management
│   │   ├── secret_management.py # Encrypted secret storage
│   │   ├── database_health.py   # Database monitoring
│   │   ├── database_backup.py   # Backup and recovery
│   │   └── migration_testing.py # Migration testing framework
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py      # Main authentication service
│   │   ├── identity_service.py  # JWT and identity management
│   │   ├── session_service.py   # Session management
│   │   ├── security_service.py  # Security features
│   │   └── user_service.py      # User management
│   ├── modules/                 # Application modules
│   │   ├── auth/                # Authentication module
│   │   ├── users/               # User management module
│   │   └── dashboard/           # Dashboard module
│   ├── main/                    # Core application components
│   │   ├── models.py            # Database models
│   │   ├── routes.py            # Main routes
│   │   └── forms.py             # WTForms
│   ├── templates/               # Jinja2 templates
│   ├── static/                  # Static assets
│   └── utils/                   # Utility functions
├── migrations/                  # Database migrations (Alembic)
├── docs/                        # Documentation
│   ├── BOILERPLATE_CHECKLIST.md # Development checklist
│   ├── BOILERPLATE_ROADMAP.md   # Development roadmap
│   ├── API_DOCUMENTATION.md     # API endpoints and usage
│   ├── DEPLOYMENT_GUIDE.md      # Deployment instructions
│   ├── DEVELOPMENT_GUIDE.md     # Development guidelines
│   └── DEFAULT_USERS.md         # Default users and credentials
├── scripts/                     # Utility scripts
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── README.md                    # This file
```

## Development

### Running Tests
```bash
pytest
pytest --cov=app  # With coverage
```

### Code Formatting
```bash
black .
isort .
```

### Database Migrations
```bash
flask db migrate -m "Description"
flask db upgrade
```

### Frontend Development
```bash
npm run dev  # Watch mode for Tailwind CSS
npm run build  # Production build
```

## CLI Commands

### Database Management
```bash
# Database health check
flask db-health

# Create database backup
flask db-backup --name my-backup

# Restore from backup
flask db-restore --file backup.sql

# List available backups
flask db-list-backups

# Clean up old backups
flask db-cleanup-backups --days 30
```

### Migration Testing
```bash
# Test all migrations
flask test-migrations

# Test specific migration
flask test-migration --revision abc123 --type upgrade

# Test migration roundtrip
flask test-migration --revision abc123 --type roundtrip
```

### Configuration Testing
```bash
# Test application configuration
flask test-config
```

### Version Management
```bash
# Show current version and phase status
python scripts/version_cli.py status

# Show detailed version information
python scripts/version_cli.py info

# Show complete version roadmap
python scripts/version_cli.py roadmap

# Complete current phase and move to next
python scripts/version_cli.py complete-phase 1

# Create release notes for a version
python scripts/version_cli.py release-notes 0.1.0
```

### TailwindCSS Management
```bash
# Build TailwindCSS (only if needed)
python scripts/version_cli.py build-tailwind

# Force rebuild TailwindCSS
python scripts/version_cli.py build-tailwind --force

# Start TailwindCSS watch mode for development
python scripts/version_cli.py watch-tailwind
```

## Configuration

### Environment Variables

#### **Core Application**
- `FLASK_ENV` - Environment (development, production, testing)
- `FLASK_DEBUG` - Debug mode (True/False)
- `SECRET_KEY` - Flask secret key (32+ characters)
- `JWT_SECRET_KEY` - JWT signing key

#### **Database Configuration**
- `DB_TYPE` - Database type (sqlite, postgresql, mysql, mariadb, mssql)
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_POOL_SIZE` - Connection pool size (default: 10)
- `DB_MAX_OVERFLOW` - Max overflow connections (default: 20)

#### **Security & Authentication**
- `IDENTITY_MANAGER_URL` - External identity manager URL
- `IDENTITY_MANAGER_API_KEY` - Identity manager API key
- `MAX_FAILED_LOGIN_ATTEMPTS` - Max failed attempts before lockout (default: 5)
- `ACCOUNT_LOCKOUT_DURATION` - Lockout duration in seconds (default: 1800)
- `BRUTE_FORCE_WINDOW` - Brute force detection window (default: 900)

#### **Caching & Sessions**
- `REDIS_URL` - Redis connection string
- `CACHE_TYPE` - Cache type (redis, simple)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 3600)

#### **Email Configuration**
- `MAIL_SERVER` - SMTP server
- `MAIL_PORT` - SMTP port (default: 587)
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password
- `MAIL_DEFAULT_SENDER` - Default sender email

## Development Roadmap

### ✅ **Phase 1: Core Foundation Infrastructure (COMPLETED)**
- **Application Architecture Setup** - Modular structure, configuration management, secret management
- **Database Architecture** - Multi-database support, health monitoring, backup/recovery, migration testing
- **Authentication & Authorization System** - JWT tokens, RBAC, security features, session management

### 🔄 **Phase 2: Core Services & Infrastructure (NEXT)**
- **API Infrastructure** - REST API, GraphQL support, API documentation
- **Communication Services** - Email service, notifications, file management
- **Caching & Performance** - Redis integration, Celery background tasks

### 📋 **Phase 3: Business Application Modules (PLANNED)**
- **Multi-Tenant Architecture** - Tenant isolation, subsidiary structure
- **Core Business Modules** - User management, contact management, document management
- **Application Templates** - Sales, finance, project management templates

### 🔗 **Phase 4: Integration Framework (PLANNED)**
- **External System Integration** - Odoo ERP, SuiteCRM, payment gateways
- **Integration Management** - Health monitoring, error handling, data synchronization

### 📊 **Phase 5: Advanced Features (PLANNED)**
- **Reporting & Analytics** - Dashboard framework, report generation
- **Workflow Automation** - Business rules engine, process automation

### 🔒 **Phase 6: Security & Compliance (PLANNED)**
- **Advanced Security** - Multi-factor authentication, security monitoring
- **Compliance Features** - Data retention, privacy controls, audit trails

### 🧪 **Phase 7: Testing & Quality Assurance (PLANNED)**
- **Comprehensive Testing** - Unit, integration, end-to-end testing
- **Quality Assurance** - Code quality metrics, performance benchmarking

### 🚀 **Phase 8: Deployment & Production (PLANNED)**
- **Infrastructure Setup** - Ansible automation, VMware/VirtualBox integration
- **Production Deployment** - Load balancer, SSL, monitoring, backup strategy

### 📚 **Phase 9: Documentation & Training (PLANNED)**
- **Technical Documentation** - API docs, architecture docs, deployment guides
- **User Documentation** - Administrator guides, end-user guides, training materials

## API Documentation
- REST API: `/api/docs`
- GraphQL Playground: `/graphql`
- OpenAPI Spec: `/api/spec`
- Database Health: `/health/database`

## Health Endpoints
- **Application Health**: `/health`
- **Database Health**: `/health/database`
- **Configuration Test**: `flask test-config`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
Business Source License 1.1 (BSL 1.1) - See LICENSE file for details

The BSL 1.1 allows free use for non-production purposes and requires a commercial license for production use. See the LICENSE file for complete terms and conditions.

## Support

For questions, issues, or contributions:
- **Documentation**: Check the `docs/` directory
- **Issues**: Create an issue in the repository
- **Development**: Follow the checklist in `docs/BOILERPLATE_CHECKLIST.md`
