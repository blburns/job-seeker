# Permission System Architecture

Comprehensive guide for setting permissions on pages, features, and modules.

## 📋 Table of Contents

1. [Permission Naming Convention](#permission-naming-convention)
2. [Permission Seeding System](#permission-seeding-system)
3. [Route Protection](#route-protection)
4. [Template-Level Permissions](#template-level-permissions)
5. [API Permissions](#api-permissions)
6. [Adding New Modules](#adding-new-modules)
7. [Permission Management](#permission-management)

---

## 🏷️ Permission Naming Convention

### **Format:** `module.action.resource`

### **Examples:**

```python
# User Management
'users.view'              # View user list
'users.view.details'      # View user details
'users.create'            # Create new users
'users.update'            # Update user info
'users.update.own'        # Update own profile only
'users.delete'            # Delete users
'users.export'            # Export user data

# Admin Module
'admin.access'            # Access admin area
'admin.dashboard.view'    # View admin dashboard
'admin.monitoring.view'   # View system monitoring

# Permissions Management
'permissions.view'        # View permissions
'permissions.create'      # Create permissions
'permissions.update'      # Update permissions
'permissions.delete'      # Delete permissions
'permissions.manage'      # Full permission management

# Roles Management
'roles.view'              # View roles
'roles.create'            # Create roles
'roles.update'            # Update roles
'roles.delete'            # Delete roles
'roles.assign'            # Assign roles to users

# Reports Module
'reports.view'            # View reports
'reports.create'          # Create reports
'reports.export'          # Export reports
'reports.schedule'        # Schedule reports

# Settings Module
'settings.view'           # View settings
'settings.update'         # Update settings
'settings.system'         # System-wide settings
'settings.security'       # Security settings
```

---

## 🌱 Permission Seeding System

### **1. Create Permission Seeds File**

```python
# scripts/seed_permissions.py
#!/usr/bin/env python3
"""
Seed all system permissions
Run this after adding new modules or features
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db
from app.services.rbac_service import rbac_service

# Define all system permissions
SYSTEM_PERMISSIONS = {
    'users': {
        'display_name': 'User Management',
        'permissions': [
            {
                'name': 'users.view',
                'display_name': 'View Users',
                'description': 'View user list and search users'
            },
            {
                'name': 'users.view.details',
                'display_name': 'View User Details',
                'description': 'View detailed user information'
            },
            {
                'name': 'users.create',
                'display_name': 'Create Users',
                'description': 'Create new user accounts'
            },
            {
                'name': 'users.update',
                'display_name': 'Update Users',
                'description': 'Update user information'
            },
            {
                'name': 'users.delete',
                'display_name': 'Delete Users',
                'description': 'Delete user accounts'
            },
            {
                'name': 'users.export',
                'display_name': 'Export Users',
                'description': 'Export user data'
            },
        ]
    },
    'admin': {
        'display_name': 'Administration',
        'permissions': [
            {
                'name': 'admin.access',
                'display_name': 'Access Admin Area',
                'description': 'Access administrative interface'
            },
            {
                'name': 'admin.dashboard.view',
                'display_name': 'View Admin Dashboard',
                'description': 'View admin dashboard and metrics'
            },
            {
                'name': 'admin.monitoring.view',
                'display_name': 'View System Monitoring',
                'description': 'View system health and monitoring'
            },
        ]
    },
    'permissions': {
        'display_name': 'Permission Management',
        'permissions': [
            {
                'name': 'permissions.view',
                'display_name': 'View Permissions',
                'description': 'View permission list'
            },
            {
                'name': 'permissions.create',
                'display_name': 'Create Permissions',
                'description': 'Create new permissions'
            },
            {
                'name': 'permissions.update',
                'display_name': 'Update Permissions',
                'description': 'Update existing permissions'
            },
            {
                'name': 'permissions.delete',
                'display_name': 'Delete Permissions',
                'description': 'Delete permissions'
            },
            {
                'name': 'permissions.manage',
                'display_name': 'Manage Permissions',
                'description': 'Full permission management access'
            },
        ]
    },
    'roles': {
        'display_name': 'Role Management',
        'permissions': [
            {
                'name': 'roles.view',
                'display_name': 'View Roles',
                'description': 'View role list'
            },
            {
                'name': 'roles.create',
                'display_name': 'Create Roles',
                'description': 'Create new roles'
            },
            {
                'name': 'roles.update',
                'display_name': 'Update Roles',
                'description': 'Update existing roles'
            },
            {
                'name': 'roles.delete',
                'display_name': 'Delete Roles',
                'description': 'Delete roles'
            },
            {
                'name': 'roles.assign',
                'display_name': 'Assign Roles',
                'description': 'Assign roles to users'
            },
        ]
    },
    'reports': {
        'display_name': 'Reports',
        'permissions': [
            {
                'name': 'reports.view',
                'display_name': 'View Reports',
                'description': 'View and access reports'
            },
            {
                'name': 'reports.create',
                'display_name': 'Create Reports',
                'description': 'Create new reports'
            },
            {
                'name': 'reports.export',
                'display_name': 'Export Reports',
                'description': 'Export report data'
            },
            {
                'name': 'reports.schedule',
                'display_name': 'Schedule Reports',
                'description': 'Schedule automated reports'
            },
        ]
    },
    'settings': {
        'display_name': 'Settings',
        'permissions': [
            {
                'name': 'settings.view',
                'display_name': 'View Settings',
                'description': 'View application settings'
            },
            {
                'name': 'settings.update',
                'display_name': 'Update Settings',
                'description': 'Update application settings'
            },
            {
                'name': 'settings.system',
                'display_name': 'System Settings',
                'description': 'Manage system-wide settings'
            },
            {
                'name': 'settings.security',
                'display_name': 'Security Settings',
                'description': 'Manage security settings'
            },
        ]
    },
}


def seed_permissions():
    """Seed all system permissions"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Seeding system permissions...")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for module_name, module_data in SYSTEM_PERMISSIONS.items():
            print(f"\n📦 Module: {module_data['display_name']}")
            
            for perm_data in module_data['permissions']:
                # Check if permission exists
                existing = rbac_service.get_permission_by_name(perm_data['name'])
                
                if existing:
                    # Update if changed
                    if (existing.display_name != perm_data['display_name'] or 
                        existing.description != perm_data.get('description')):
                        rbac_service.update_permission(
                            existing.id,
                            display_name=perm_data['display_name'],
                            description=perm_data.get('description')
                        )
                        print(f"  ✓ Updated: {perm_data['name']}")
                        updated_count += 1
                    else:
                        print(f"  - Exists: {perm_data['name']}")
                        skipped_count += 1
                else:
                    # Create new permission
                    rbac_service.create_permission(
                        name=perm_data['name'],
                        display_name=perm_data['display_name'],
                        module=module_name,
                        description=perm_data.get('description'),
                        is_active=True
                    )
                    print(f"  ✓ Created: {perm_data['name']}")
                    created_count += 1
        
        print(f"\n✅ Permission seeding complete!")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {created_count + updated_count + skipped_count}")


if __name__ == '__main__':
    seed_permissions()
```

---

## 🛡️ Route Protection

### **Method 1: Decorator-Based (Recommended)**

```python
from app.utils.rbac_decorators import permission_required, role_required

# Single permission
@app.route('/users')
@login_required
@permission_required('users.view')
def list_users():
    return render_template('users/list.html')

# Multiple permissions (ANY)
@app.route('/users/export')
@login_required
@permission_required('users.export', 'admin.access')
def export_users():
    return send_file('users.csv')

# Multiple permissions (ALL) - use multiple decorators
@app.route('/users/bulk-delete')
@login_required
@permission_required('users.delete')
@permission_required('users.manage')
def bulk_delete_users():
    # User must have BOTH permissions
    pass

# Role-based
@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

# Admin/Superadmin only
@app.route('/admin/system')
@login_required
@admin_required()
def system_settings():
    return render_template('admin/system.html')
```

### **Method 2: Manual Check**

```python
from flask_login import current_user

@app.route('/users/<user_id>')
@login_required
def view_user(user_id):
    # Check permission
    if not current_user.has_permission('users.view.details'):
        flash('You do not have permission to view user details', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if viewing own profile or has permission
    if str(current_user.id) != user_id:
        if not current_user.has_permission('users.view'):
            abort(403)
    
    user = User.query.get_or_404(user_id)
    return render_template('users/view.html', user=user)
```

### **Method 3: Before Request Hook**

```python
from flask import Blueprint, g

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.before_request
def check_users_access():
    """Check if user has access to users module"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # Allow access to own profile
    if request.endpoint == 'users.profile':
        return None
    
    # Check module access
    if not current_user.has_permission('users.view'):
        flash('You do not have access to the users module', 'danger')
        return redirect(url_for('main.index'))
```

---

## 🎨 Template-Level Permissions

### **Check Permissions in Templates**

```jinja2
{# Check single permission #}
{% if current_user.has_permission('users.create') %}
  <a href="{{ url_for('users.create') }}" class="btn btn-primary">
    <i class="ti ti-plus"></i> Create User
  </a>
{% endif %}

{# Check multiple permissions (OR) #}
{% if current_user.has_permission('users.update') or current_user.has_permission('users.delete') %}
  <div class="actions">
    {% if current_user.has_permission('users.update') %}
      <button class="btn btn-sm btn-warning">Edit</button>
    {% endif %}
    {% if current_user.has_permission('users.delete') %}
      <button class="btn btn-sm btn-danger">Delete</button>
    {% endif %}
  </div>
{% endif %}

{# Check role #}
{% if current_user.has_role('admin') %}
  <div class="admin-panel">
    <!-- Admin-only content -->
  </div>
{% endif %}

{# Check admin status #}
{% if current_user.is_admin or current_user.is_superadmin %}
  <a href="{{ url_for('admin.dashboard') }}">Admin Dashboard</a>
{% endif %}

{# Hide entire sections #}
{% if current_user.has_permission('reports.view') %}
  <div class="card">
    <div class="card-header">Reports</div>
    <div class="card-body">
      <!-- Reports content -->
    </div>
  </div>
{% endif %}
```

### **Create Permission Helper Macro**

```jinja2
{# templates/macros/permissions.html #}
{% macro has_any_permission(permissions) %}
  {% set has_perm = namespace(value=False) %}
  {% for perm in permissions %}
    {% if current_user.has_permission(perm) %}
      {% set has_perm.value = True %}
    {% endif %}
  {% endfor %}
  {{ has_perm.value }}
{% endmacro %}

{# Usage #}
{% from 'macros/permissions.html' import has_any_permission %}

{% if has_any_permission(['users.create', 'users.update', 'users.delete']) %}
  <div class="user-management">
    <!-- Content -->
  </div>
{% endif %}
```

---

## 🔌 API Permissions

### **API Route Protection**

```python
from app.utils.rbac_decorators import permission_required

# API endpoint with permission
@api_bp.route('/users', methods=['GET'])
@login_required
@permission_required('users.view', api_mode=True)
def api_list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

# API endpoint with multiple permissions
@api_bp.route('/users/<user_id>', methods=['DELETE'])
@login_required
@permission_required('users.delete', api_mode=True)
def api_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200
```

### **API Response Format**

```python
# Success (200)
{
    "data": [...],
    "message": "Success"
}

# Unauthorized (401)
{
    "error": "Authentication required",
    "message": "Please log in to access this resource"
}

# Forbidden (403)
{
    "error": "Permission denied",
    "message": "You do not have permission to perform this action",
    "required_permission": "users.delete"
}
```

---

## ➕ Adding New Modules

### **Step-by-Step Guide**

#### **1. Define Module Permissions**

Add to `scripts/seed_permissions.py`:

```python
SYSTEM_PERMISSIONS = {
    # ... existing modules ...
    
    'products': {
        'display_name': 'Product Management',
        'permissions': [
            {
                'name': 'products.view',
                'display_name': 'View Products',
                'description': 'View product catalog'
            },
            {
                'name': 'products.create',
                'display_name': 'Create Products',
                'description': 'Add new products'
            },
            {
                'name': 'products.update',
                'display_name': 'Update Products',
                'description': 'Edit product information'
            },
            {
                'name': 'products.delete',
                'display_name': 'Delete Products',
                'description': 'Remove products'
            },
            {
                'name': 'products.manage.inventory',
                'display_name': 'Manage Inventory',
                'description': 'Manage product inventory'
            },
            {
                'name': 'products.manage.pricing',
                'display_name': 'Manage Pricing',
                'description': 'Update product pricing'
            },
        ]
    },
}
```

#### **2. Run Permission Seeder**

```bash
python scripts/seed_permissions.py
```

#### **3. Create Module Blueprint**

```python
# app/modules/products/__init__.py
from flask import Blueprint

products_bp = Blueprint('products', __name__, url_prefix='/products')

from . import routes
```

#### **4. Add Protected Routes**

```python
# app/modules/products/routes.py
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.modules.products import products_bp
from app.utils.rbac_decorators import permission_required

@products_bp.route('/')
@login_required
@permission_required('products.view')
def list_products():
    """List all products"""
    return render_template('products/list.html')

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('products.create')
def create_product():
    """Create new product"""
    if request.method == 'POST':
        # Handle creation
        pass
    return render_template('products/create.html')

@products_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('products.update')
def edit_product(product_id):
    """Edit product"""
    return render_template('products/edit.html')

@products_bp.route('/<product_id>/delete', methods=['POST'])
@login_required
@permission_required('products.delete')
def delete_product(product_id):
    """Delete product"""
    # Handle deletion
    return redirect(url_for('products.list_products'))
```

#### **5. Register Blueprint**

```python
# app/extensions/blueprints.py
try:
    from app.modules.products import products_bp
    HAS_PRODUCTS = True
except ImportError:
    HAS_PRODUCTS = False

def register_blueprints(app):
    # ... existing blueprints ...
    
    if HAS_PRODUCTS:
        app.register_blueprint(products_bp)
```

#### **6. Add to Sidebar Menu**

```python
# config/modules.py
MODULES = [
    # ... existing modules ...
    
    {
        'name': 'products',
        'display_name': 'Products',
        'description': 'Product management',
        'icon': 'package',
        'color': 'success',
        'permission': 'products.view',
        'blueprint_name': 'products',
        'route': 'list_products',
        'sort_order': 50,
        'section': 'apps',
        'parent': None,
        'children': [
            {'name': 'list', 'display_name': 'All Products', 'route': 'list_products'},
            {'name': 'create', 'display_name': 'Add Product', 'route': 'create_product'},
            {'name': 'categories', 'display_name': 'Categories', 'route': 'list_categories'},
        ]
    },
]
```

#### **7. Create Templates with Permission Checks**

```jinja2
{# templates/products/list.html #}
{% extends "base.html" %}

{% block content %}
<div class="row">
  <div class="col-md-12">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h4>Products</h4>
      
      {% if current_user.has_permission('products.create') %}
        <a href="{{ url_for('products.create_product') }}" class="btn btn-primary">
          <i class="ti ti-plus"></i> Add Product
        </a>
      {% endif %}
    </div>
    
    <div class="card">
      <div class="card-body">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Price</th>
              <th>Stock</th>
              {% if current_user.has_permission('products.update') or current_user.has_permission('products.delete') %}
                <th>Actions</th>
              {% endif %}
            </tr>
          </thead>
          <tbody>
            {% for product in products %}
              <tr>
                <td>{{ product.name }}</td>
                <td>${{ product.price }}</td>
                <td>{{ product.stock }}</td>
                {% if current_user.has_permission('products.update') or current_user.has_permission('products.delete') %}
                  <td>
                    {% if current_user.has_permission('products.update') %}
                      <a href="{{ url_for('products.edit_product', product_id=product.id) }}" 
                         class="btn btn-sm btn-warning">Edit</a>
                    {% endif %}
                    {% if current_user.has_permission('products.delete') %}
                      <button class="btn btn-sm btn-danger" 
                              onclick="deleteProduct('{{ product.id }}')">Delete</button>
                    {% endif %}
                  </td>
                {% endif %}
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

## 🎛️ Permission Management

### **Assign Permissions to Roles**

```python
# Via RBAC Service
from app.services.rbac_service import rbac_service

# Create role
role = rbac_service.create_role(
    name='product_manager',
    display_name='Product Manager',
    description='Manages product catalog'
)

# Assign permissions
rbac_service.assign_permission_to_role(role.id, 'products.view')
rbac_service.assign_permission_to_role(role.id, 'products.create')
rbac_service.assign_permission_to_role(role.id, 'products.update')
rbac_service.assign_permission_to_role(role.id, 'products.manage.inventory')
rbac_service.assign_permission_to_role(role.id, 'products.manage.pricing')
```

### **Assign Role to User**

```python
# Via RBAC Service
rbac_service.assign_role_to_user(
    user_id=user.id,
    role_id=role.id,
    assigned_by_id=current_user.id,
    expires_at=None  # Never expires
)
```

### **Via Admin UI**

1. Navigate to `/admin/roles`
2. Click on role
3. Click "Manage Permissions"
4. Select permissions
5. Save

---

## 📊 Permission Hierarchy

### **Inheritance Pattern**

```python
# General to Specific
'products.view'              # Can view products
'products.view.details'      # Can view detailed product info
'products.view.analytics'    # Can view product analytics

# Module-based
'admin.access'               # Can access admin area
'admin.dashboard.view'       # Can view admin dashboard
'admin.monitoring.view'      # Can view monitoring

# Action-based
'users.create'               # Can create users
'users.update'               # Can update users
'users.update.own'           # Can only update own profile
'users.delete'               # Can delete users
```

### **Wildcard Permissions (Future)**

```python
# Not yet implemented, but planned:
'products.*'                 # All product permissions
'admin.*'                    # All admin permissions
'*.view'                     # All view permissions
```

---

## 🔍 Permission Checking Best Practices

### **1. Always Check in Routes**
```python
@permission_required('resource.action')
```

### **2. Check in Templates for UI**
```jinja2
{% if current_user.has_permission('resource.action') %}
```

### **3. Check in Business Logic**
```python
if not current_user.has_permission('resource.action'):
    raise PermissionError('Insufficient permissions')
```

### **4. Fail Securely**
```python
# Default to deny
if not current_user.has_permission('resource.action'):
    abort(403)
```

### **5. Log Permission Denials**
```python
logger.warning(f"Permission denied: {current_user.username} tried to access {request.endpoint}")
```

---

## 🚀 Quick Start Checklist

For adding a new module with permissions:

- [ ] Define permissions in `seed_permissions.py`
- [ ] Run `python scripts/seed_permissions.py`
- [ ] Create module blueprint
- [ ] Add `@permission_required()` decorators to routes
- [ ] Add permission checks in templates
- [ ] Register blueprint in `blueprints.py`
- [ ] Add module to `config/modules.py`
- [ ] Create default roles with permissions
- [ ] Test permission enforcement
- [ ] Document module permissions

---

This system provides **complete permission control** over every page, feature, and module in your application! 🎉
