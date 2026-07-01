# Module Development Guide

## Overview

This guide explains how to create new modules for the application. Modules are self-contained features that include routes, API endpoints, templates, and database models.

## Module Structure

A complete module consists of:

```
app/modules/module_name/
├── __init__.py          # Blueprint exports
├── routes.py            # Web routes (HTML)
└── api.py               # API routes (JSON)

app/templates/modules/module_name/
├── dashboard.html       # Module dashboard
├── list.html            # List view
├── create.html          # Create form
├── edit.html            # Edit form
├── view.html            # Detail view
└── settings.html        # Settings page

app/models/             # Database models (if needed)
└── module_name.py       # Module-specific models
```

## Step-by-Step: Creating a New Module

### Step 1: Create Module Directory

```bash
mkdir -p app/modules/products
mkdir -p app/templates/modules/products
```

### Step 2: Create Blueprint Files

**`app/modules/products/__init__.py`:**
```python
from app.modules.products.routes import products_bp
from app.modules.products.api import products_api_bp

__all__ = ['products_bp', 'products_api_bp']
```

**`app/modules/products/routes.py`:**
```python
import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user
from app.extensions.core import db

logger = logging.getLogger(__name__)
products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
@login_required
def index():
    """Redirect to products dashboard"""
    return redirect(url_for('products.dashboard'))

@products_bp.route('/dashboard')
@login_required
def dashboard():
    """Products dashboard"""
    # Check permission
    if not current_user.has_permission('products.view'):
        flash('You do not have permission to view products', 'danger')
        return redirect(url_for('main.index'))
    
    # Get products data
    # products = Product.query.all()
    
    return render_template('modules/products/dashboard.html')

@products_bp.route('/list')
@login_required
def list_products():
    """List all products"""
    if not current_user.has_permission('products.view'):
        flash('Permission denied', 'danger')
        return redirect(url_for('products.dashboard'))
    
    return render_template('modules/products/list.html')

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_product():
    """Create new product"""
    if not current_user.has_permission('products.create'):
        flash('Permission denied', 'danger')
        return redirect(url_for('products.list_products'))
    
    if request.method == 'POST':
        # Handle form submission
        flash('Product created successfully', 'success')
        return redirect(url_for('products.list_products'))
    
    return render_template('modules/products/create.html')

@products_bp.route('/<uuid:product_id>')
@login_required
def view_product(product_id):
    """View product details"""
    if not current_user.has_permission('products.view'):
        flash('Permission denied', 'danger')
        return redirect(url_for('products.list_products'))
    
    # product = Product.query.get_or_404(product_id)
    return render_template('modules/products/view.html', product_id=product_id)

@products_bp.route('/<uuid:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    if not current_user.has_permission('products.update'):
        flash('Permission denied', 'danger')
        return redirect(url_for('products.view_product', product_id=product_id))
    
    if request.method == 'POST':
        # Handle form submission
        flash('Product updated successfully', 'success')
        return redirect(url_for('products.view_product', product_id=product_id))
    
    # product = Product.query.get_or_404(product_id)
    return render_template('modules/products/edit.html', product_id=product_id)
```

**`app/modules/products/api.py`:**
```python
import logging
from flask import jsonify, request, Blueprint
from flask_login import login_required, current_user
from app.extensions.core import db

logger = logging.getLogger(__name__)
products_api_bp = Blueprint('products_api', __name__, url_prefix='/api/products')

@products_api_bp.route('/', methods=['GET'])
@login_required
def list_products():
    """List products API"""
    if not current_user.has_permission('products.view'):
        return jsonify({'error': 'Permission denied'}), 403
    
    # products = Product.query.all()
    return jsonify({'products': []})

@products_api_bp.route('/', methods=['POST'])
@login_required
def create_product():
    """Create product API"""
    if not current_user.has_permission('products.create'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    # Create product logic
    return jsonify({'status': 'success', 'product': {}}), 201
```

### Step 3: Register Blueprint

**`app/extensions/blueprints.py`:**
```python
# Add conditional import
try:
    from app.modules.products import products_bp, products_api_bp
    HAS_PRODUCTS = True
except ImportError:
    HAS_PRODUCTS = False

# In register_blueprints function:
if HAS_PRODUCTS:
    app.register_blueprint(products_bp)
    app.register_blueprint(products_api_bp)
```

### Step 4: Add Module Configuration

**`config/modules.py`:**
```python
MODULES = [
    # ... existing modules ...
    {
        'name': 'products',
        'display_name': 'Products',
        'description': 'Product management',
        'icon': 'box',
        'color': 'blue',
        'permission': 'products.view',
        'blueprint_name': 'products',
        'route': 'dashboard',
        'sort_order': 40,
        'section': 'business',
        'parent': None,
        'children': [
            {'name': 'products_dashboard', 'display_name': 'Dashboard', 'route': 'dashboard', 'icon': 'dashboard'},
            {'name': 'products_list', 'display_name': 'List Products', 'route': 'list_products', 'icon': 'list'},
            {'name': 'products_create', 'display_name': 'Create Product', 'route': 'create_product', 'icon': 'plus'},
        ]
    },
]
```

### Step 5: Create Database Models (if needed)

**`app/models/products.py`:**
```python
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions.core import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin

class Product(BaseModel, SoftDeleteMixin):
    """Product model"""
    __tablename__ = 'products'
    __table_args__ = {'schema': 'products'}  # Or use existing schema
    
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    # ... other fields
    
    def __repr__(self):
        return f'<Product {self.name}>'
```

**Update `app/models/__init__.py`:**
```python
try:
    from .products import Product
except ImportError:
    pass
```

### Step 6: Create Templates

**`app/templates/modules/products/dashboard.html`:**
```jinja2
{% extends "base_metronic.html" %}

{% block title %}Products Dashboard{% endblock %}

{% block content %}
<div class="kt-container-fixed">
    <div class="kt-card">
        <div class="kt-card-content p-5">
            <h1 class="text-2xl font-semibold mb-4">Products Dashboard</h1>
            <!-- Dashboard content -->
        </div>
    </div>
</div>
{% endblock %}
```

Create similar templates for `list.html`, `create.html`, `edit.html`, `view.html`, `settings.html`.

### Step 7: Create Database Schema (if needed)

If your module needs its own schema:

```bash
# Create migration
flask db migrate -m "Add products schema"

# Or use schema migration script
# Add to SCHEMA_MAPPING in scripts/migrate_to_schemas.py
```

### Step 8: Add Permissions to Roles

```python
# Update default roles or create new role
role = Role.query.filter_by(name='manager').first()
permissions = role.permissions or {}
permissions['products'] = ['view', 'create', 'update', 'delete']
role.permissions = permissions
db.session.commit()
```

## Module Template Generator

Use the provided script to generate module scaffolding:

```bash
python3 scripts/create_module_from_template.py products
```

This creates:
- Module directory structure
- Basic route files
- Basic template files
- Module configuration entry

## Best Practices

### 1. Permission Checks

Always check permissions:
```python
@login_required
def my_route():
    if not current_user.has_permission('module.action'):
        flash('Permission denied', 'danger')
        return redirect(url_for('module.dashboard'))
```

### 2. Error Handling

Use try/except blocks:
```python
try:
    # Database operation
    db.session.commit()
    flash('Success', 'success')
except Exception as e:
    logger.exception('Error in route')
    db.session.rollback()
    flash('Error occurred', 'danger')
```

### 3. Logging

Log important actions:
```python
logger.info(f'User {current_user.username} created product {product.id}')
logger.error('Failed to create product', exc_info=True)
```

### 4. Template Inheritance

Always extend `base_metronic.html`:
```jinja2
{% extends "base_metronic.html" %}
```

### 5. URL Building

Use `url_for` with blueprint prefix:
```python
url_for('products.dashboard')  # /products/dashboard
url_for('products.view_product', product_id=product.id)
```

### 6. Form Handling

Use Flask-WTF for forms:
```python
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Save')
```

## Module Checklist

- [ ] Module directory created
- [ ] Blueprint files created (`__init__.py`, `routes.py`, `api.py`)
- [ ] Blueprints registered in `blueprints.py`
- [ ] Module added to `config/modules.py`
- [ ] Templates created (dashboard, list, create, edit, view, settings)
- [ ] Database models created (if needed)
- [ ] Database schema created (if needed)
- [ ] Permissions added to roles
- [ ] Routes tested
- [ ] API endpoints tested
- [ ] Templates styled with Metronic
- [ ] Documentation updated

## Common Patterns

### List View with Pagination

```python
from flask import request

@products_bp.route('/list')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Product.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('modules/products/list.html', 
                         products=pagination.items,
                         pagination=pagination)
```

### Search and Filter

```python
@products_bp.route('/list')
@login_required
def list_products():
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category_id=category)
    
    products = query.all()
    return render_template('modules/products/list.html', products=products)
```

### Bulk Operations

```python
@products_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    if not current_user.has_permission('products.delete'):
        return jsonify({'error': 'Permission denied'}), 403
    
    product_ids = request.json.get('ids', [])
    Product.query.filter(Product.id.in_(product_ids)).delete()
    db.session.commit()
    
    return jsonify({'status': 'success'})
```

## Testing Modules

### Unit Tests

```python
# tests/unit/test_products.py
def test_create_product(client, auth):
    auth.login()
    response = client.post('/products/create', data={
        'name': 'Test Product',
        'price': '99.99'
    })
    assert response.status_code == 302
    assert Product.query.filter_by(name='Test Product').first() is not None
```

### Integration Tests

```python
# tests/integration/test_products_api.py
def test_products_api_list(client, auth):
    auth.login()
    response = client.get('/api/products/')
    assert response.status_code == 200
    assert 'products' in response.json
```

## See Also

- [RBAC_GUIDE.md](RBAC_GUIDE.md) - Permission system
- [DATABASE_SCHEMAS.md](DATABASE_SCHEMAS.md) - Database structure
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API development
