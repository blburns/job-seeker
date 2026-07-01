# Database Recreation Test

## Overview
This document tests whether the database can be recreated from scratch using migrations.

## Test Process

### 1. Check Current Database State
```bash
flask db current
flask db history
```

### 2. Backup Current Database
```bash
# Backup is automatically created in app/data/db/backups/
```

### 3. Reset Database (Options)

#### Option A: Via Flask Migrate
```bash
# Drop and recreate
flask db downgrade base
flask db upgrade
```

#### Option B: Via Script
```bash
python scripts/reset_database.py --confirm
```

#### Option C: Manual SQL
```bash
# For SQLite
rm app/data/app.db

# For PostgreSQL
psql -d database_name -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### 4. Verify Recreation
```bash
# Check migrations applied
flask db current

# Verify data
python scripts/manage_permissions.py --show

# Test application
flask run
```

## Migration Sequence

The database will be created in this order:

1. **0001_initial_schema.py** - Core auth tables
2. **0002_add_auth_data.py** - Seed roles, groups, users
3. **0003_add_contacts.py** - Contact tables
4. **0004_add_contacts_data.py** - Contact data
5. **0005_add_documents.py** - Document tables
6. **0006_add_documents_data.py** - Document data
7. **0007_add_settings.py** - Settings tables
8. **0008_add_settings_data.py** - Settings data
9. **0009_add_tenants.py** - Tenant tables
10. **0010_add_tenants_data.py** - Tenant data
11. **0011_add_organizations.py** - Organization tables
12. **0012_add_organizations_data.py** - Organization data

## Expected Results

After recreation, you should have:

✅ **Tables Created:**
- users, roles, groups
- user_roles, user_groups, group_roles
- contact_categories, contacts, contact_communications
- document_categories, documents, document_access_logs
- setting_categories, settings, setting_values
- tenants, tenant_invitations, tenant_settings
- organizations, brands, organization_members

✅ **Data Seeded:**
- 5 roles (super_admin, admin, manager, user, viewer)
- 3 groups (system_admins, content_managers, regular_users)
- 3 users (super_admin, admin, regular_user)
- Multiple setting categories and settings

✅ **Permissions Ready:**
- All roles have default permissions
- Can login with super_admin account
- All migrations apply successfully

## Verification Checklist

- [ ] All migrations applied
- [ ] All tables created
- [ ] Seed data inserted
- [ ] Can login with super_admin
- [ ] Permissions system working
- [ ] All modules accessible
- [ ] No errors in logs

