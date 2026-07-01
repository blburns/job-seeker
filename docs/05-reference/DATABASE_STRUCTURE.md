# Database Structure Documentation

## Overview
This document describes the database structure for the Flask boilerplate application.

## Database Type
- **Primary Database**: PostgreSQL (configurable to MySQL, MS SQL Server, SQLite)
- **ORM**: SQLAlchemy
- **UUID Primary Keys**: All tables use UUID (PostgreSQL UUID type) as primary keys

---

## Core Tables

### 1. `users` Table
**Purpose**: User accounts and authentication

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | uuid.uuid4() | Primary key |
| `username` | VARCHAR(64) | NO | - | Unique username, indexed |
| `email` | VARCHAR(120) | NO | - | Unique email, indexed |
| `password_hash` | VARCHAR(256) | NO | - | Bcrypt hashed password |
| `is_active` | BOOLEAN | YES | TRUE | Account active status |
| `is_admin` | BOOLEAN | YES | FALSE | Admin privileges |
| `is_superadmin` | BOOLEAN | YES | FALSE | Super admin privileges |
| `email_verified` | BOOLEAN | YES | FALSE | Email verification status |
| `email_verification_token` | VARCHAR(255) | YES | NULL | Email verification token |
| `email_verification_expires` | TIMESTAMP | YES | NULL | Token expiration |
| `password_reset_token` | VARCHAR(255) | YES | NULL | Password reset token |
| `password_reset_expires` | TIMESTAMP | YES | NULL | Reset token expiration |
| `last_login` | TIMESTAMP | YES | NULL | Last login timestamp |
| `last_activity` | TIMESTAMP | YES | NULL | Last activity timestamp |
| `failed_login_attempts` | INTEGER | YES | 0 | Failed login counter |
| `last_failed_login` | TIMESTAMP | YES | NULL | Last failed login attempt |
| `lockout_until` | TIMESTAMP | YES | NULL | Account lockout expiration |
| `firstname` | VARCHAR(64) | YES | NULL | First name |
| `lastname` | VARCHAR(64) | YES | NULL | Last name |
| `display_name` | VARCHAR(64) | YES | NULL | Display name |
| `avatar_path` | VARCHAR(255) | YES | NULL | Profile photo path (relative to static) |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | datetime.utcnow | Last update timestamp |

**Indexes**:
- Primary key: `id`
- Unique: `username`, `email`
- Index: `username`, `email`

**Methods**:
- `set_password(password)` - Hash and set password
- `check_password(password)` - Verify password
- `get_full_name()` - Get user's full name
- `is_locked_out()` - Check if account is locked
- `increment_failed_login()` - Increment failed attempts (locks after 5)
- `reset_failed_login()` - Reset failed attempts
- `has_permission(permission)` - Check RBAC permission
- `has_role(role_name)` - Check if user has role
- `is_module_visible(module_name)` - Check module visibility

---

### 2. `roles` Table
**Purpose**: Role-Based Access Control (RBAC) roles

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | uuid.uuid4() | Primary key |
| `name` | VARCHAR(64) | NO | - | Unique role name |
| `display_name` | VARCHAR(64) | YES | NULL | Display name |
| `description` | TEXT | YES | NULL | Role description |
| `permissions` | JSON | YES | NULL | Permission structure |
| `priority` | INTEGER | YES | 0 | Role priority |
| `is_system_role` | BOOLEAN | YES | FALSE | System role flag |
| `is_active` | BOOLEAN | YES | TRUE | Active status |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | datetime.utcnow | Last update timestamp |

**Indexes**:
- Primary key: `id`
- Unique: `name`

**Relationships**:
- Many-to-Many with `users` (via `user_roles`)
- Many-to-Many with `groups` (via `group_roles`)

**Permissions Structure** (JSON):
```json
{
  "module_name": ["action1", "action2"],
  "users": ["view", "create", "update", "delete"],
  "accounts": ["view", "create", "update"]
}
```

---

### 3. `groups` Table
**Purpose**: User groups for organizing users

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | uuid.uuid4() | Primary key |
| `name` | VARCHAR(64) | NO | - | Unique group name |
| `display_name` | VARCHAR(64) | YES | NULL | Display name |
| `description` | TEXT | YES | NULL | Group description |
| `is_active` | BOOLEAN | YES | TRUE | Active status |
| `is_system_group` | BOOLEAN | YES | FALSE | System group flag |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |
| `updated_at` | TIMESTAMP | YES | datetime.utcnow | Last update timestamp |

**Indexes**:
- Primary key: `id`
- Unique: `name`

**Relationships**:
- Many-to-Many with `users` (via `user_groups`)
- Many-to-Many with `roles` (via `group_roles`)

---

## Association Tables

### 4. `user_groups` Table
**Purpose**: Many-to-many relationship between users and groups

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | UUID | NO | - | Foreign key to `users.id` |
| `group_id` | UUID | NO | - | Foreign key to `groups.id` |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |

**Primary Key**: (`user_id`, `group_id`)

---

### 5. `user_roles` Table
**Purpose**: Many-to-many relationship between users and roles

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | UUID | NO | - | Foreign key to `users.id` |
| `role_id` | UUID | NO | - | Foreign key to `roles.id` |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |

**Primary Key**: (`user_id`, `role_id`)

---

### 6. `group_roles` Table
**Purpose**: Many-to-many relationship between groups and roles

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `group_id` | UUID | NO | - | Foreign key to `groups.id` |
| `role_id` | UUID | NO | - | Foreign key to `roles.id` |
| `created_at` | TIMESTAMP | YES | datetime.utcnow | Creation timestamp |

**Primary Key**: (`group_id`, `role_id`)

---

## Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│    users    │         │  user_roles  │         │    roles    │
├─────────────┤         ├──────────────┤         ├─────────────┤
│ id (PK)     │◄────────┤ user_id (FK) │         │ id (PK)     │
│ username    │         │ role_id (FK) │────────►│ name        │
│ email       │         └──────────────┘         │ permissions │
│ password    │                                  │ ...         │
│ ...         │                                  └─────────────┘
└─────────────┘                                           ▲
      │                                                   │
      │                                                   │
      │         ┌──────────────┐                          │
      │         │ user_groups  │                          │
      └─────────┤ user_id (FK) │                          │
                │ group_id (FK)│                          │
                └──────────────┘                          │
                         │                                │
                         │                                │
                         ▼                                │
                ┌─────────────┐                           │
                │   groups    │                           │
                ├─────────────┤                           │
                │ id (PK)     │                           │
                │ name        │                           │
                │ ...         │                           │
                └─────────────┘                           │
                         │                                │
                         │         ┌──────────────┐       │
                         └────────►│ group_roles  │───────┘
                                   │ group_id (FK)│
                                   │ role_id (FK) │
                                   └──────────────┘
```

---

## Security Features

### Account Lockout
- After 5 failed login attempts, account is locked for 30 minutes
- Lockout tracked via `lockout_until` timestamp
- Failed attempts tracked in `failed_login_attempts`

### Password Security
- Passwords stored as bcrypt hashes (256 chars)
- Password reset tokens with expiration
- Password reset via `password_reset_token` and `password_reset_expires`

### Email Verification
- Email verification tokens with expiration
- Tracked via `email_verified`, `email_verification_token`, `email_verification_expires`

---

## RBAC (Role-Based Access Control)

### Permission Structure
Permissions are stored as JSON in the `roles.permissions` column:
```json
{
  "module_name": ["action1", "action2"],
  "users": ["view", "create", "update", "delete"],
  "accounts": ["view", "create", "update"]
}
```

### Permission Checking
Users can have permissions through:
1. **Direct roles** - Roles assigned directly to user
2. **Group roles** - Roles assigned to groups the user belongs to

### Permission Format
- Format: `module.action` (e.g., `users.view`, `accounts.create`)
- Module mapping for backward compatibility
- Action mapping: `read` → `view`, `edit` → `update`

---

## Notes

1. **UUID Primary Keys**: All tables use UUID for primary keys (PostgreSQL UUID type)
2. **Timestamps**: All tables have `created_at` and `updated_at` timestamps
3. **Soft Deletes**: Not implemented in core tables (can be added per module)
4. **Indexes**: Username and email are indexed for fast lookups
5. **Relationships**: All relationships use SQLAlchemy relationships with proper back_populates

---

## Future Extensions

The following modules may have their own models (not yet implemented in this boilerplate):
- **Accounts** - Business account management
- **Contacts** - Contact management
- **Documents** - Document/file management
- **Organizations** - Organization management
- **Tenants** - Multi-tenancy support

These would be added as separate model files following the same patterns.
