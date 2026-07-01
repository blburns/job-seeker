# RBAC Quick Start Guide

Get started with the Role-Based Access Control system in minutes!

---

## Setup

### 1. Run Database Migration

```bash
python scripts/add_rbac_tables.py
```

This creates:
- ✅ 4 RBAC tables
- ✅ All necessary indexes
- ✅ 19 default permissions

### 2. Verify Installation

```bash
python -c "from app.services.rbac_service import rbac_service; print('Permissions:', len(rbac_service.get_all_permissions()))"
```

Should output: `Permissions: 19`

---

## Quick Usage

### Protect Routes with Permissions

```python
from flask import Blueprint
from flask_login import login_required
from app.utils.rbac_decorators import permission_required

bp = Blueprint('products', __name__)

@bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@permission_required('products.create')
def create_product():
    # Only users with 'products.create' permission can access
    return render_template('products/create.html')
```

### Check Permissions in Templates

```jinja2
{% if current_user.has_permission('users.create') %}
  <a href="{{ url_for('users.create') }}" class="btn btn-primary">
    Create User
  </a>
{% endif %}
```

### Use RBAC Service

```python
from app.services.rbac_service import rbac_service

# Create a permission
permission = rbac_service.create_permission(
    name='products.create',
    display_name='Create Products',
    module='products'
)

# Create a role
role = rbac_service.create_role(
    name='product_manager',
    display_name='Product Manager'
)

# Assign permission to role
rbac_service.assign_permission_to_role(role.id, permission.id)

# Assign role to user
rbac_service.assign_role_to_user(
    user_id=user.id,
    role_id=role.id,
    assigned_by_id=admin.id
)
```

---

## Admin Interface

### Access Admin Panel

1. Login as admin user
2. Navigate to: `http://localhost:5000/admin`

### Manage Permissions

- **List**: `/admin/permissions`
- **Create**: `/admin/permissions/create`
- **Edit**: `/admin/permissions/<id>/edit`

### Manage Roles

- **List**: `/admin/roles`
- **Create**: `/admin/roles/create`
- **View**: `/admin/roles/<id>`
- **Edit**: `/admin/roles/<id>/edit`
- **Permissions**: `/admin/roles/<id>/permissions`

### Assign Roles to Users

- **Manage**: `/admin/users/<id>/roles`
- **Assign**: POST to `/admin/users/<id>/roles/assign`
- **Revoke**: POST to `/admin/users/<id>/roles/<role_id>/revoke`

---

## Available Decorators

### Permission-Based

```python
# Single permission required
@permission_required('users.create')

# Any of multiple permissions
@any_permission_required('users.view', 'users.create')

# All permissions required
@all_permissions_required('users.view', 'users.update')
```

### Role-Based

```python
# Specific role required
@role_required('admin')

# Admin access
@admin_required()

# Superadmin access
@superadmin_required()
```

### API Mode

```python
# Returns JSON instead of redirect
@permission_required('users.view', api_mode=True)
def api_get_users():
    return jsonify({'users': [...]})
```

---

## Default Permissions

### Users Module
- `users.view` - View users
- `users.create` - Create users
- `users.update` - Update users
- `users.delete` - Delete users
- `users.activate` - Activate/deactivate users

### Roles Module
- `roles.view` - View roles
- `roles.create` - Create roles
- `roles.update` - Update roles
- `roles.delete` - Delete roles
- `roles.assign` - Assign roles to users

### Permissions Module
- `permissions.view` - View permissions
- `permissions.manage` - Manage permissions

### Groups Module
- `groups.view` - View groups
- `groups.create` - Create groups
- `groups.update` - Update groups
- `groups.delete` - Delete groups

### Settings Module
- `settings.view` - View settings
- `settings.update` - Update settings

### Audit Module
- `audit.view` - View audit logs

---

## Common Tasks

### Create a New Permission

```python
from app.services.rbac_service import rbac_service

permission = rbac_service.create_permission(
    name='products.create',
    display_name='Create Products',
    module='products',
    description='Allows creating new products',
    category='management'
)
```

### Create a Role with Permissions

```python
# Create role
role = rbac_service.create_role(
    name='product_manager',
    display_name='Product Manager',
    description='Manages product catalog'
)

# Get permissions
view_perm = rbac_service.get_permission(name='products.view')
create_perm = rbac_service.get_permission(name='products.create')
update_perm = rbac_service.get_permission(name='products.update')

# Assign permissions
rbac_service.assign_permission_to_role(role.id, view_perm.id)
rbac_service.assign_permission_to_role(role.id, create_perm.id)
rbac_service.assign_permission_to_role(role.id, update_perm.id)
```

### Assign Role with Expiration

```python
from datetime import datetime, timedelta

rbac_service.assign_role_to_user(
    user_id=user.id,
    role_id=role.id,
    assigned_by_id=current_user.id,
    expires_at=datetime.utcnow() + timedelta(days=90),
    notes='Temporary assignment for Q1 project'
)
```

### Check User Permissions

```python
# In code
if current_user.has_permission('products.create'):
    # User can create products
    pass

# Get all permissions
permissions = current_user.get_all_permissions()
# Returns: ['products.view', 'products.create', ...]
```

### Revoke Role

```python
rbac_service.revoke_role_from_user(
    user_id=user.id,
    role_id=role.id,
    revoked_by_id=current_user.id,
    reason='Project completed'
)
```

---

## API Endpoints

All API endpoints require authentication and appropriate permissions.

### Get All Permissions

```bash
GET /admin/api/permissions
```

Response:
```json
{
  "permissions": [
    {
      "id": "...",
      "name": "users.view",
      "display_name": "View Users",
      "module": "users",
      ...
    }
  ]
}
```

### Get All Roles

```bash
GET /admin/api/roles
```

### Get Role Permissions

```bash
GET /admin/api/roles/<role_id>/permissions
```

### Get User Permissions

```bash
GET /admin/api/users/<user_id>/permissions
```

### Get RBAC Statistics

```bash
GET /admin/api/stats
```

Response:
```json
{
  "total_permissions": 19,
  "active_permissions": 19,
  "total_roles": 5,
  "active_roles": 5,
  "total_assignments": 10,
  "active_assignments": 8,
  "expired_assignments": 2,
  "role_hierarchies": 0
}
```

---

## Troubleshooting

### Permissions Not Working

**Issue**: User has role but permission check fails

**Solution**:
1. Verify role has permission: `/admin/roles/<id>`
2. Check role assignment is active: `/admin/users/<id>/roles`
3. Check assignment hasn't expired
4. Verify permission is active

### Admin Panel Not Accessible

**Issue**: Cannot access `/admin`

**Solution**:
1. Ensure user is admin: `user.is_admin = True`
2. Or assign admin role with appropriate permissions
3. Check logs for permission denials

### Migration Failed

**Issue**: Database migration errors

**Solution**:
```bash
# Check if tables already exist
psql -d your_database -c "\dt auth.*"

# If tables exist, migration is already done
# If not, check database connection and permissions
```

---

## Best Practices

### Permission Naming

Use format: `module.action`

**Good:**
- `users.view`
- `products.create`
- `orders.update`
- `reports.export`

**Bad:**
- `view_users` (no module)
- `users` (no action)
- `user.view` (singular module)

### Role Design

**Principle of Least Privilege:**
- Give users only permissions they need
- Create specific roles for specific tasks
- Use role expiration for temporary access

**Role Examples:**
- `viewer` - Read-only access
- `editor` - Create and update
- `manager` - Full CRUD + assign
- `admin` - System administration

### Assignment Management

**Always include:**
- `assigned_by_id` - Track who assigned
- `notes` - Document why assigned
- `expires_at` - For temporary access

**Regular Maintenance:**
```python
# Clean up expired assignments
from app.services.rbac_service import rbac_service
cleaned = rbac_service.cleanup_expired_assignments()
print(f"Cleaned up {cleaned} expired assignments")
```

---

## Next Steps

1. **Create Your Permissions**
   - Define permissions for your modules
   - Use consistent naming conventions
   - Group by module

2. **Design Your Roles**
   - Create roles based on job functions
   - Assign appropriate permissions
   - Test access levels

3. **Assign Roles to Users**
   - Use admin interface or service
   - Set expiration dates when appropriate
   - Document assignments

4. **Protect Your Routes**
   - Add decorators to routes
   - Check permissions in templates
   - Test access control

5. **Monitor and Maintain**
   - Review assignments regularly
   - Clean up expired assignments
   - Audit permission usage

---

## Related Documentation

- [RBAC Complete Guide](../../06-planning/PHASE_1_2_RBAC_COMPLETE.md)
- [Implementation TODO](../../06-planning/IMPLEMENTATION_TODO.md)
- [Quick Start Guide](../../../QUICK_START.md)

---

**Ready to secure your application with RBAC!** 🔒
