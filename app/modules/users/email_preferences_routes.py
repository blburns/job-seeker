"""
Email Preferences Routes
Manage user email preferences and unsubscribe
"""

import logging
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.extensions.core import db
from app.modules.users import users_bp
from app.models.email_log import EmailPreference

logger = logging.getLogger(__name__)


@users_bp.route('/settings/email-preferences', methods=['GET', 'POST'])
@login_required
def email_preferences():
    """Manage email preferences"""
    try:
        # Get or create preferences
        preferences = EmailPreference.get_or_create(current_user.id)
        
        if request.method == 'POST':
            # Update preferences
            preferences.marketing_emails = request.form.get('marketing_emails') == 'on'
            preferences.product_updates = request.form.get('product_updates') == 'on'
            preferences.newsletter = request.form.get('newsletter') == 'on'
            preferences.order_notifications = request.form.get('order_notifications') == 'on'
            preferences.account_notifications = request.form.get('account_notifications') == 'on'
            preferences.email_frequency = request.form.get('email_frequency', 'immediate')
            
            db.session.commit()
            
            flash('Email preferences updated successfully', 'success')
            return redirect(url_for('users.email_preferences'))
        
        return render_template('modules/users/settings/email_preferences.html',
                             preferences=preferences)
    except Exception as e:
        logger.exception('Error managing email preferences')
        flash('An error occurred updating your preferences', 'danger')
        return redirect(url_for('users.settings'))


@users_bp.route('/unsubscribe/<token>')
def unsubscribe(token):
    """Unsubscribe from all emails"""
    try:
        preferences = EmailPreference.get_by_token(token)
        
        if not preferences:
            flash('Invalid unsubscribe link', 'danger')
            return redirect(url_for('main.index'))
        
        if request.method == 'POST' or request.args.get('confirm') == '1':
            preferences.unsubscribe_all_emails()
            
            return render_template('modules/users/unsubscribe_success.html',
                                 user=preferences.user)
        
        return render_template('modules/users/unsubscribe_confirm.html',
                             user=preferences.user,
                             token=token)
    except Exception as e:
        logger.exception('Error unsubscribing')
        flash('An error occurred', 'danger')
        return redirect(url_for('main.index'))


@users_bp.route('/resubscribe/<token>')
def resubscribe(token):
    """Resubscribe to emails"""
    try:
        preferences = EmailPreference.get_by_token(token)
        
        if not preferences:
            flash('Invalid link', 'danger')
            return redirect(url_for('main.index'))
        
        preferences.resubscribe()
        
        flash('You have been resubscribed to our emails', 'success')
        return redirect(url_for('users.email_preferences') if preferences.user == current_user else url_for('main.index'))
    except Exception as e:
        logger.exception('Error resubscribing')
        flash('An error occurred', 'danger')
        return redirect(url_for('main.index'))
