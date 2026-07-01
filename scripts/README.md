# Scripts Directory

This directory contains utility scripts for managing the application.

## Available Scripts

### manage_permissions.py
**Purpose**: Manage role permissions and restore defaults when site breaks

**Usage**:
```bash
# Show current permissions for all roles
python scripts/manage_permissions.py --show

# Reset all roles to default permissions
python scripts/manage_permissions.py --reset-all

# Reset specific role
python scripts/manage_permissions.py --reset-role admin

# Restore safe defaults (use when site breaks)
python scripts/manage_permissions.py --restore-safe
```

**Features**:
- Shows current permissions for all roles
- Resets permissions to safe defaults
- Restore permissions when site breaks
- Per-role or all-roles reset capability

**Default Permission Levels**:
- **super_admin**: Full access to everything
- **admin**: Administrative access (read/update, limited delete)
- **manager**: Content management (contacts, documents)
- **user**: Standard user access (create/read/update)
- **viewer**: Read-only access

---

### backup_database.py
**Purpose**: Create database backups

**Usage**:
```bash
python scripts/backup_database.py
```

**Features**:
- Creates SQL dump with timestamp
- Creates schema-only backup
- Copies database file (for SQLite)
- Stores in `app/data/db/backups/`

---

### check_database_tables.py
**Purpose**: Inspect current database state

**Usage**:
```bash
python scripts/check_database_tables.py
```

**Features**:
- Lists all database tables
- Shows connection status
- Displays table details

---

## Quick Commands

```bash
# Check database connection
python scripts/check_database_tables.py

# Backup database
python scripts/backup_database.py

# Show permissions
python scripts/manage_permissions.py --show

# Emergency: Restore permissions
python scripts/manage_permissions.py --restore-safe
```

## Emergency Procedures

### Site Breaks - Restore Permissions
```bash
python scripts/manage_permissions.py --restore-safe
```

### Lost Database - Restore Backup
```bash
# Find latest backup
ls -ltr app/data/db/backups/

# Restore (adjust path as needed)
psql -d your_database -f app/data/db/backups/latest_backup.sql
```

### Reset Everything
```bash
# Backup first
python scripts/backup_database.py

# Reset permissions
python scripts/manage_permissions.py --reset-all

# Re-run migrations
flask db downgrade base
flask db upgrade
```

