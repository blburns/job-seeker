# Database Schema Migration Guide

## Overview

This guide documents the migration of database tables from the `public` schema to logical schemas for better organization, RBAC compliance, and scalability.

## Schema Organization

Tables are organized into 7 logical schemas:

1. **`auth`** - Authentication and RBAC (6 tables)
2. **`accounts`** - Business account management (5 tables)
3. **`contacts`** - Contact management (4 tables)
4. **`documents`** - Document/file management (5 tables)
5. **`organizations`** - Organization and brand management (3 tables)
6. **`tenants`** - Multi-tenancy support (4 tables)
7. **`settings`** - Application settings (5 tables)
8. **`public`** - System tables (1 table: `alembic_version`)

## Migration Process

### Prerequisites

1. **Backup your database** before running the migration:
   ```bash
   pg_dump -U postgres -d your_database > backup_before_migration.sql
   ```

2. Ensure you have PostgreSQL superuser privileges or sufficient permissions to:
   - Create schemas
   - Move tables between schemas
   - Modify foreign key constraints

### Step 1: Dry Run

Always run a dry run first to preview changes:

```bash
python3 scripts/migrate_to_schemas.py --dry-run
```

This will show you:
- Which schemas will be created
- Which tables will be moved
- Any potential issues

### Step 2: Run Migration

Once you've reviewed the dry run output, run the actual migration:

```bash
python3 scripts/migrate_to_schemas.py --confirm
```

**Important**: The `--confirm` flag is required to prevent accidental migrations.

### Step 3: Verify Migration

After migration, verify the tables are in the correct schemas:

```sql
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY table_schema, table_name;
```

## Model Updates

### New Model Structure

Models have been reorganized into `app/models/` directory:

```
app/models/
├── __init__.py          # Main exports
├── base.py              # Base model classes
├── auth.py              # Auth schema models
├── accounts.py          # Accounts schema models
├── contacts.py          # Contacts schema models
├── documents.py         # Documents schema models
├── organizations.py     # Organizations schema models
├── tenants.py           # Tenants schema models
└── settings.py          # Settings schema models
```

### Import Changes

**Old import** (still works for backward compatibility):
```python
from app.main.models import User, Role, Group
```

**New import** (recommended):
```python
from app.models.auth import User, Role, Group
from app.models.accounts import Account, AccountType
from app.models.contacts import Contact, ContactCategory
# etc.
```

### Schema Specification

All models now specify their schema using `__table_args__`:

```python
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}
    # ...
```

## Foreign Key References

Foreign keys automatically use schema-qualified names. For example:

```python
# In accounts schema, referencing auth.users
created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'), nullable=True)

# In organizations schema, referencing tenants.tenants
tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.tenants.id'), nullable=False)
```

PostgreSQL handles cross-schema foreign keys automatically, but you must use the fully qualified name (`schema.table`) in your model definitions.

## RBAC Compliance

The schema organization supports RBAC (Role-Based Access Control) by:

1. **Logical Separation**: Auth tables are isolated in the `auth` schema
2. **Permission Structure**: Roles have JSON permissions that reference modules
3. **Cross-Schema Access**: Foreign keys maintain relationships while allowing schema-level permissions

### Permission Format

Permissions are stored in JSON format:
```json
{
  "module_name": ["action1", "action2"],
  "users": ["view", "create", "update", "delete"],
  "accounts": ["view", "create"]
}
```

### Checking Permissions

```python
from app.models.auth import User

user = User.query.first()
if user.has_permission('accounts.view'):
    # User can view accounts
    pass
```

## Benefits

1. **Organization**: Tables grouped by functional domain
2. **Security**: Schema-level permissions possible
3. **Maintainability**: Easier to understand and maintain
4. **Scalability**: Easy to add new modules with their own schemas
5. **Multi-tenancy**: Can support tenant-specific schemas if needed
6. **Backup/Restore**: Can backup/restore individual schemas

## Rollback

If you need to rollback the migration:

1. **Restore from backup**:
   ```bash
   psql -U postgres -d your_database < backup_before_migration.sql
   ```

2. **Or manually move tables back**:
   ```sql
   ALTER TABLE auth.users SET SCHEMA public;
   ALTER TABLE accounts.accounts SET SCHEMA public;
   -- etc. for all tables
   ```

## Troubleshooting

### Error: "schema does not exist"

If you get this error, ensure the migration script created all schemas. You can manually create them:

```sql
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS accounts;
CREATE SCHEMA IF NOT EXISTS contacts;
CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS organizations;
CREATE SCHEMA IF NOT EXISTS tenants;
CREATE SCHEMA IF NOT EXISTS settings;
```

### Error: "permission denied"

Ensure your database user has sufficient privileges:
```sql
GRANT ALL ON SCHEMA auth TO your_user;
GRANT ALL ON SCHEMA accounts TO your_user;
-- etc.
```

### Foreign Key Errors

If foreign keys fail after migration, verify they use schema-qualified names:
```sql
SELECT 
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## Post-Migration Checklist

- [ ] Verify all tables are in correct schemas
- [ ] Test application startup
- [ ] Test authentication/login
- [ ] Test RBAC permissions
- [ ] Test CRUD operations for each module
- [ ] Verify foreign key relationships work
- [ ] Update any custom SQL queries to use schema-qualified names
- [ ] Update database backup scripts if needed

## Support

For issues or questions:
1. Check the dry run output for warnings
2. Review PostgreSQL logs
3. Verify model imports work correctly
4. Test with a development database first
