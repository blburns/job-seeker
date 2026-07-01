#!/usr/bin/env python3
"""
Generate permission template for a new module

Usage:
    python scripts/generate_module_permissions.py <module_name> <display_name>
    
Example:
    python scripts/generate_module_permissions.py products "Product Management"
"""

import sys

PERMISSION_TEMPLATE = """
    '{module_name}': {{
        'display_name': '{display_name}',
        'permissions': [
            {{
                'name': '{module_name}.view',
                'display_name': 'View {display_name}',
                'description': 'View {module_name} list and search'
            }},
            {{
                'name': '{module_name}.view.details',
                'display_name': 'View {display_name} Details',
                'description': 'View detailed {module_name} information'
            }},
            {{
                'name': '{module_name}.create',
                'display_name': 'Create {display_name}',
                'description': 'Create new {module_name}'
            }},
            {{
                'name': '{module_name}.update',
                'display_name': 'Update {display_name}',
                'description': 'Update {module_name} information'
            }},
            {{
                'name': '{module_name}.delete',
                'display_name': 'Delete {display_name}',
                'description': 'Delete {module_name}'
            }},
            {{
                'name': '{module_name}.export',
                'display_name': 'Export {display_name}',
                'description': 'Export {module_name} data'
            }},
        ]
    }},
"""

ROUTE_TEMPLATE = """
# app/modules/{module_name}/routes.py
from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.modules.{module_name} import {module_name}_bp
from app.utils.rbac_decorators import permission_required
from app.extensions.core import db

@{module_name}_bp.route('/')
@login_required
@permission_required('{module_name}.view')
def list_{module_name}():
    \"\"\"List all {module_name}\"\"\"
    # TODO: Implement list logic
    return render_template('{module_name}/list.html')

@{module_name}_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('{module_name}.create')
def create_{module_singular}():
    \"\"\"Create new {module_singular}\"\"\"
    if request.method == 'POST':
        # TODO: Implement creation logic
        flash('{display_name} created successfully', 'success')
        return redirect(url_for('{module_name}.list_{module_name}'))
    return render_template('{module_name}/create.html')

@{module_name}_bp.route('/<{module_singular}_id>')
@login_required
@permission_required('{module_name}.view.details')
def view_{module_singular}({module_singular}_id):
    \"\"\"View {module_singular} details\"\"\"
    # TODO: Implement view logic
    return render_template('{module_name}/view.html')

@{module_name}_bp.route('/<{module_singular}_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('{module_name}.update')
def edit_{module_singular}({module_singular}_id):
    \"\"\"Edit {module_singular}\"\"\"
    if request.method == 'POST':
        # TODO: Implement update logic
        flash('{display_name} updated successfully', 'success')
        return redirect(url_for('{module_name}.view_{module_singular}', {module_singular}_id={module_singular}_id))
    return render_template('{module_name}/edit.html')

@{module_name}_bp.route('/<{module_singular}_id>/delete', methods=['POST'])
@login_required
@permission_required('{module_name}.delete')
def delete_{module_singular}({module_singular}_id):
    \"\"\"Delete {module_singular}\"\"\"
    # TODO: Implement deletion logic
    flash('{display_name} deleted successfully', 'success')
    return redirect(url_for('{module_name}.list_{module_name}'))

@{module_name}_bp.route('/export')
@login_required
@permission_required('{module_name}.export')
def export_{module_name}():
    \"\"\"Export {module_name} data\"\"\"
    # TODO: Implement export logic
    return jsonify({{'message': 'Export not yet implemented'}}), 501
"""

BLUEPRINT_TEMPLATE = """
# app/modules/{module_name}/__init__.py
from flask import Blueprint

{module_name}_bp = Blueprint('{module_name}', __name__, url_prefix='/{module_name}')

from . import routes
"""

MENU_CONFIG_TEMPLATE = """
# Add to config/modules.py MODULES list:
    {{
        'name': '{module_name}',
        'display_name': '{display_name}',
        'description': '{display_name} module',
        'icon': 'package',  # Change icon as needed
        'color': 'info',
        'permission': '{module_name}.view',
        'blueprint_name': '{module_name}',
        'route': 'list_{module_name}',
        'sort_order': 50,  # Adjust as needed
        'section': 'apps',
        'parent': None,
        'children': [
            {{'name': 'list', 'display_name': 'All {display_name}', 'route': 'list_{module_name}'}},
            {{'name': 'create', 'display_name': 'Create {display_name}', 'route': 'create_{module_singular}'}},
        ]
    }},
"""

BLUEPRINT_REGISTRATION_TEMPLATE = """
# Add to app/extensions/blueprints.py:

try:
    from app.modules.{module_name} import {module_name}_bp
    HAS_{module_name_upper} = True
except ImportError:
    HAS_{module_name_upper} = False

# In register_blueprints() function:
    if HAS_{module_name_upper}:
        app.register_blueprint({module_name}_bp)
"""


def generate_module_permissions(module_name, display_name):
    """Generate permission template for a module"""
    
    # Generate singular form (simple approach)
    module_singular = module_name.rstrip('s')
    module_name_upper = module_name.upper()
    
    print("=" * 80)
    print(f"📦 Generating permissions for: {display_name} ({module_name})")
    print("=" * 80)
    
    print("\n1️⃣  Add to scripts/seed_permissions.py SYSTEM_PERMISSIONS:")
    print("-" * 80)
    print(PERMISSION_TEMPLATE.format(
        module_name=module_name,
        display_name=display_name
    ))
    
    print("\n2️⃣  Create Blueprint:")
    print("-" * 80)
    print(BLUEPRINT_TEMPLATE.format(module_name=module_name))
    
    print("\n3️⃣  Create Routes with Permissions:")
    print("-" * 80)
    print(ROUTE_TEMPLATE.format(
        module_name=module_name,
        module_singular=module_singular,
        display_name=display_name
    ))
    
    print("\n4️⃣  Register Blueprint:")
    print("-" * 80)
    print(BLUEPRINT_REGISTRATION_TEMPLATE.format(
        module_name=module_name,
        module_name_upper=module_name_upper
    ))
    
    print("\n5️⃣  Add to Sidebar Menu:")
    print("-" * 80)
    print(MENU_CONFIG_TEMPLATE.format(
        module_name=module_name,
        module_singular=module_singular,
        display_name=display_name
    ))
    
    print("\n6️⃣  Next Steps:")
    print("-" * 80)
    print(f"  1. Create directory: app/modules/{module_name}/")
    print(f"  2. Create __init__.py with blueprint")
    print(f"  3. Create routes.py with protected routes")
    print(f"  4. Create templates in: app/templates/{module_name}/")
    print(f"  5. Run: python scripts/seed_permissions.py")
    print(f"  6. Register blueprint in app/extensions/blueprints.py")
    print(f"  7. Add to config/modules.py")
    print(f"  8. Create default roles with permissions")
    print("=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/generate_module_permissions.py <module_name> <display_name>")
        print("Example: python scripts/generate_module_permissions.py products \"Product Management\"")
        sys.exit(1)
    
    module_name = sys.argv[1].lower()
    display_name = sys.argv[2]
    
    generate_module_permissions(module_name, display_name)
