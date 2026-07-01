# RBAC-Only Application Structure

## Overview

This application has been streamlined to focus exclusively on **Role-Based Access Control (RBAC)** functionality. All non-essential modules have been removed, leaving only the core authentication and RBAC management features.

## Core Modules

### 1. **auth** - Authentication
**Purpose:** User authentication and session management

**Routes:**
- `/auth/login` - User login
- `/auth/register` - User registration
- `/auth/logout` - User logout
- `/auth/forgot_password` - Password reset request
- `/auth/reset_password/<token>` - Password reset

**Features:**
- Secure password hashing (bcrypt)
- Account lockout protection
- Password strength validation
- Email verification (optional)
- Session management

### 2. **users** - RBAC Management
**Purpose:** Complete RBAC system management (Users, Roles, Groups)

**Routes:**
- `/users/dashboard` - RBAC overview dashboard
- `/users/list` - List all users
- `/users/create` - Create new user
- `/users/<id>/view` - View user details
- `/users/<id>/edit` - Edit user
- `/users/roles` - List roles
- `/users/groups` - List groups
- `/users/permissions` - Manage permissions
- `/users/profile` - User profile

**Features:**
- User CRUD operations
- Role management
- Group management
- Permission assignment
- User-role-group relationships
- Profile management

### 3. **main** - Dashboard
**Purpose:** Main application dashboard

**Routes:**
- `/` - Home/Dashboard

## Removed Modules

The following modules have been removed to focus on RBAC:

- ❌ `accounts` - Business account management
- ❌ `contacts` - Contact management
- ❌ `documents` - Document management
- ❌ `organizations` - Organization management
- ❌ `tenants` - Multi-tenancy
- ❌ `settings` - Application settings
- ❌ `account` - User account pages
- ❌ `network` - Social network
- ❌ `profile` - Public profiles
- ❌ `security` - Security logs (integrated into users)
- ❌ `store` - E-commerce
- ❌ `email_relay` - Email services
- ❌ `dashboard` - Separate dashboard module (using main)

## Database Schema

Only the **`auth`** schema is used:

```
auth/
├── users          → User accounts
├── roles          → RBAC roles
├── groups         → User groups
├── user_roles      → User-Role associations
├── user_groups     → User-Group associations
└── group_roles     → Group-Role associations
```

All other schemas (accounts, contacts, documents, organizations, tenants, settings) are **not used** in this RBAC-only version.

## Module Structure

```
app/modules/
├── auth/
│   ├── __init__.py
│   ├── routes.py      → Authentication routes
│   └── api.py         → Authentication API
│
└── users/
    ├── __init__.py
    ├── routes.py      → User/Role/Group management routes
    └── api.py         → RBAC API endpoints
```

## Configuration

### Blueprints (`app/extensions/blueprints.py`)
Only registers:
- `main_bp` - Main dashboard
- `auth_bp` - Authentication
- `users_bp` - RBAC management

### Modules (`config/modules.py`)
Only defines:
- `dashboard` - Main dashboard
- `users` - RBAC management (includes roles/groups/permissions)

## Menu Structure

Simplified sidebar menu:

```
📊 Dashboards
  └── Dashboard

👥 RBAC Management
  └── Users
      ├── Dashboard
      ├── List Users
      ├── Create User
      ├── Roles
      ├── Groups
      ├── Permissions
      └── My Profile
```

## API Endpoints

### Authentication API (`/api/v1/auth/`)
- `POST /login` - Authenticate
- `POST /logout` - Logout
- `POST /register` - Register user
- `POST /forgot_password` - Request password reset
- `POST /reset_password` - Reset password

### RBAC API (`/api/v1/users/`)
- `GET /users` - List users
- `POST /users` - Create user
- `GET /users/<id>` - Get user
- `PUT /users/<id>` - Update user
- `DELETE /users/<id>` - Delete user
- `GET /roles` - List roles
- `POST /roles` - Create role
- `GET /groups` - List groups
- `POST /groups` - Create group

## Permissions

Permission format: `module.action`

**Available Permissions:**
- `users.view` - View users
- `users.create` - Create users
- `users.update` - Update users
- `users.delete` - Delete users
- `roles.view` - View roles
- `roles.manage` - Manage roles
- `groups.view` - View groups
- `groups.manage` - Manage groups

## Usage

### For New Applications

1. Start with this RBAC-only boilerplate
2. Add your custom modules as needed
3. Use the RBAC system for all permission checks

### For Existing Applications

1. Remove non-RBAC modules
2. Update blueprints registration
3. Update module configuration
4. Simplify menu structure

## Benefits

✅ **Focused** - Only RBAC features, no bloat  
✅ **Simple** - Easy to understand and maintain  
✅ **Fast** - Minimal dependencies and overhead  
✅ **Secure** - Complete RBAC implementation  
✅ **Extensible** - Easy to add custom modules later  

## Next Steps

To add custom modules:

1. Create module in `app/modules/your_module/`
2. Add to `app/extensions/blueprints.py`
3. Add to `config/modules.py`
4. Use RBAC permissions for access control

## See Also

- [RBAC_GUIDE.md](../03-development/rbac/RBAC_GUIDE.md) - Complete RBAC documentation
- [AUTHENTICATION.md](../03-development/auth/AUTHENTICATION.md) - Authentication guide
- [MODULE_DEVELOPMENT.md](../03-development/MODULE_DEVELOPMENT.md) - Adding modules
