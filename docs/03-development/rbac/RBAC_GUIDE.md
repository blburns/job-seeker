# RBAC (Role-Based Access Control) Guide

## Overview

This application implements a comprehensive Role-Based Access Control (RBAC) system that allows fine-grained permission management through roles and groups.

## Core Concepts

### Users
Individual user accounts with authentication credentials.

### Roles
Collections of permissions. Users can have multiple roles.

### Groups
Collections of users. Groups can have roles, which are inherited by all group members.

### Permissions
Granular access controls in the format: `module.action`

Examples:
- `users.view` - View users
- `users.create` - Create users
- `accounts.edit` - Edit accounts
- `documents.delete` - Delete documents

## Permission Structure

Permissions are stored as JSON in the `roles` table:

```json
{
  "users": ["view", "create", "update", "delete"],
  "accounts": ["view", "create", "update"],
  "documents": ["view"],
  "settings": ["view", "update"]
}
```

### Permission Format

```
{module_name}.{action}
```

**Modules:**
- `users` - User management
- `accounts` - Business accounts
- `contacts` - Contact management
- `documents` - Document management
- `organizations` - Organization management
- `tenants` - Tenant management
- `settings` - Application settings

**Actions:**
- `view` - Read/view data
- `create` - Create new records
- `update` - Edit existing records
- `delete` - Delete records
- `manage` - Full management (all actions)

## Default Roles

The system includes these default roles (created by `create_default_roles_groups.py`):

### 1. Super Admin
- **Permissions:** All permissions on all modules
- **Access:** Full system access
- **Use Case:** System administrators

### 2. Admin
- **Permissions:** Most permissions except system-level settings
- **Access:** User and content management
- **Use Case:** Application administrators

### 3. Manager
- **Permissions:** View and edit permissions on business modules
- **Access:** Accounts, contacts, documents
- **Use Case:** Department managers

### 4. User
- **Permissions:** View permissions on most modules
- **Access:** Read-only access to most content
- **Use Case:** Regular users

### 5. Viewer
- **Permissions:** View-only permissions
- **Access:** Read-only access
- **Use Case:** Auditors, read-only users

## Using RBAC in Code

### Check Permissions in Routes

```python
from flask_login import login_required, current_user

@users_bp.route('/create')
@login_required
def create_user():
    # Check permission
    if not current_user.has_permission('users.create'):
        flash('You do not have permission to create users', 'danger')
        return redirect(url_for('users.dashboard'))
    
    # User has permission, proceed
    return render_template('modules/users/create.html')
```

### Check Permissions in Templates

```jinja2
{% if current_user.has_permission('users.create') %}
    <a href="{{ url_for('users.create') }}" class="btn">Create User</a>
{% endif %}
```

### Check Roles

```python
# Check if user has a specific role
if current_user.has_role('admin'):
    # Admin-specific logic
    pass
```

### Module Visibility

```python
# Check if module should be visible to user
if current_user.is_module_visible('accounts'):
    # Show accounts module in menu
    pass
```

## Permission Inheritance

### Direct Role Permissions
Permissions assigned directly to a user's roles.

### Group Role Permissions
Permissions from roles assigned to groups the user belongs to.

**Example:**
```
User: john
  ├── Direct Role: "user" → permissions: ["users.view"]
  └── Group: "managers"
      └── Role: "manager" → permissions: ["accounts.view", "accounts.edit"]
      
Result: john has ["users.view", "accounts.view", "accounts.edit"]
```

## Creating Custom Roles

### Via Script

```python
from app.models.auth import Role, db

# Create new role
role = Role(
    name='content_editor',
    display_name='Content Editor',
    description='Can edit content but not delete',
    permissions={
        'documents': ['view', 'create', 'update'],
        'contacts': ['view', 'update']
    },
    priority=5,
    is_active=True
)
db.session.add(role)
db.session.commit()
```

### Via Management Script

```bash
python3 scripts/manage_permissions.py --create-role content_editor
```

## Permission Checking Methods

### User.has_permission(permission: str) -> bool

Checks if user has a specific permission.

```python
user.has_permission('users.create')  # True/False
```

**Logic:**
1. Super admins always return `True`
2. Admins return `True` for most permissions
3. Check direct role permissions
4. Check group role permissions
5. Return `False` if not found

### User.has_role(role_name: str) -> bool

Checks if user has a specific role (direct or via group).

```python
user.has_role('admin')  # True/False
```

### User.is_module_visible(module_name: str) -> bool

Checks if a module should be visible in the UI for this user.

```python
user.is_module_visible('accounts')  # True/False
```

## Permission Mapping

The system includes backward compatibility mapping for permission names:

**Module Mapping:**
- `contact` → `contacts`
- `document` → `documents`
- `user` → `users`
- `account` → `accounts`

**Action Mapping:**
- `read` → `view`
- `edit` → `update`

## Admin Privileges

### Super Admin (`is_superadmin=True`)
- All permissions automatically granted
- Cannot be restricted
- System-level access

### Admin (`is_admin=True`)
- Most permissions automatically granted
- Can be restricted by settings
- Application-level access

## Best Practices

### 1. Use Permission Checks

Always check permissions before allowing actions:

```python
@route('/delete/<id>')
@login_required
def delete(id):
    if not current_user.has_permission('module.delete'):
        abort(403)
    # Proceed with deletion
```

### 2. Check at Route Level

Use decorators or route-level checks:

```python
from functools import wraps

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@route('/create')
@require_permission('users.create')
def create():
    pass
```

### 3. Template-Level Checks

Hide UI elements users can't use:

```jinja2
{% if current_user.has_permission('users.create') %}
    <button>Create User</button>
{% endif %}
```

### 4. API Permission Checks

Check permissions in API endpoints:

```python
@api.route('/users')
class UserList(Resource):
    @login_required
    def get(self):
        if not current_user.has_permission('users.view'):
            return {'error': 'Permission denied'}, 403
        # Return users
```

## Permission Management

### Viewing Permissions

```bash
# View all roles and permissions
python3 scripts/manage_permissions.py --show

# View user permissions
python3 scripts/manage_permissions.py --user <username>
```

### Assigning Roles

```python
from app.models.auth import User, Role, db

user = User.query.filter_by(username='john').first()
role = Role.query.filter_by(name='manager').first()

user.roles.append(role)
db.session.commit()
```

### Assigning Groups

```python
from app.models.auth import User, Group, db

user = User.query.filter_by(username='john').first()
group = Group.query.filter_by(name='managers').first()

user.groups.append(group)
db.session.commit()
```

## Security Considerations

1. **Always Check Permissions** - Never trust client-side checks alone
2. **Principle of Least Privilege** - Grant minimum necessary permissions
3. **Regular Audits** - Review permissions periodically
4. **Role Hierarchy** - Use priority to establish role hierarchy
5. **System Roles** - Mark system roles (`is_system_role=True`) to prevent deletion

## Troubleshooting

### Permission Not Working

1. Check user has the role: `user.has_role('role_name')`
2. Check role has the permission: `role.permissions`
3. Check group roles if user is in groups
4. Verify permission format: `module.action`
5. Check admin flags: `is_superadmin` or `is_admin`

### Module Not Visible

1. Check `is_module_visible()` method
2. Verify module permission in `config/modules.py`
3. Check user has required permission
4. Verify module is active in configuration

## Examples

### Example: Content Manager Role

```python
content_manager = Role(
    name='content_manager',
    display_name='Content Manager',
    permissions={
        'documents': ['view', 'create', 'update', 'delete'],
        'contacts': ['view', 'create', 'update'],
        'accounts': ['view']
    }
)
```

### Example: Department-Specific Access

```python
# Create department group
sales_group = Group(name='sales', display_name='Sales Department')

# Create sales-specific role
sales_role = Role(
    name='sales_rep',
    permissions={
        'accounts': ['view', 'create', 'update'],
        'contacts': ['view', 'create', 'update'],
        'documents': ['view']
    }
)

# Assign role to group
sales_group.roles.append(sales_role)

# Add users to group
user.groups.append(sales_group)
```

## See Also

- [DATABASE_SCHEMAS.md](../../05-reference/DATABASE_SCHEMAS.md) - Database structure
- [MODULE_DEVELOPMENT.md](../MODULE_DEVELOPMENT.md) - Adding permissions to modules
- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - API permission checks
