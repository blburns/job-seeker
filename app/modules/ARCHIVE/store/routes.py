"""
Store module routes
E-commerce store, shopping cart, checkout, and orders
"""

import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create store blueprint
store_bp = Blueprint('store', __name__, url_prefix='/store')


@store_bp.route('/')
def index():
    """Store home page"""
    return render_template('modules/store/home.html')


@store_bp.route('/cart')
@login_required
def cart():
    """Shopping cart"""
    return render_template('modules/store/shopping_cart.html')


@store_bp.route('/wishlist')
@login_required
def wishlist():
    """Wishlist"""
    return render_template('modules/store/wishlist.html')


@store_bp.route('/my-orders')
@login_required
def my_orders():
    """User orders"""
    return render_template('modules/store/my_orders.html')


@store_bp.route('/product/<product_id>')
def product_details(product_id):
    """Product details page"""
    return render_template('modules/store/product_details.html', product_id=product_id)


@store_bp.route('/search')
def search():
    """Product search"""
    search_type = request.args.get('type', 'grid')  # grid or list
    return render_template(f'modules/store/search_results_{search_type}.html')


@store_bp.route('/order-receipt/<order_id>')
@login_required
def order_receipt(order_id):
    """Order receipt"""
    return render_template('modules/store/order_receipt.html', order_id=order_id)
