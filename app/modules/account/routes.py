"""
Account module routes
User account management, settings, billing, security, and team management
"""

import logging
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create account blueprint
account_bp = Blueprint('account', __name__, url_prefix='/account')


@account_bp.route('/')
@login_required
def index():
    """Account index - redirects to home"""
    return redirect(url_for('account.home'))


@account_bp.route('/home')
@login_required
def home():
    """Account home/dashboard"""
    return render_template('modules/account/home.html')


@account_bp.route('/activity')
@login_required
def activity():
    """Account activity log"""
    return render_template('modules/account/activity.html')


@account_bp.route('/api-keys')
@login_required
def api_keys():
    """API keys management"""
    return render_template('modules/account/api_keys.html')


@account_bp.route('/appearance')
@login_required
def appearance():
    """Appearance settings"""
    return render_template('modules/account/appearance.html')


@account_bp.route('/integrations')
@login_required
def integrations():
    """Integrations management"""
    return render_template('modules/account/integrations.html')


@account_bp.route('/notifications')
@login_required
def notifications():
    """Notification settings"""
    return render_template('modules/account/notifications.html')


@account_bp.route('/invite-a-friend')
@login_required
def invite_a_friend():
    """Invite a friend page"""
    return render_template('modules/account/invite_a_friend.html')


# Account Home Routes
@account_bp.route('/home/get-started')
@login_required
def get_started():
    """Get started page"""
    return render_template('modules/account/home/get_started.html')


@account_bp.route('/home/user-profile')
@login_required
def user_profile():
    """User profile settings"""
    return render_template('modules/account/home/user_profile.html')


@account_bp.route('/home/company-profile')
@login_required
def company_profile():
    """Company profile settings"""
    return render_template('modules/account/home/company_profile.html')


@account_bp.route('/home/settings-sidebar')
@login_required
def settings_sidebar():
    """Settings with sidebar"""
    return render_template('modules/account/home/settings_sidebar.html')


@account_bp.route('/home/settings-enterprise')
@login_required
def settings_enterprise():
    """Enterprise settings"""
    return render_template('modules/account/home/settings_enterprise.html')


@account_bp.route('/home/settings-plain')
@login_required
def settings_plain():
    """Plain settings"""
    return render_template('modules/account/home/settings_plain.html')


@account_bp.route('/home/settings-modal')
@login_required
def settings_modal():
    """Settings modal"""
    return render_template('modules/account/home/settings_modal.html')


# Billing Routes
@account_bp.route('/billing/basic')
@login_required
def billing_basic():
    """Basic billing"""
    return render_template('modules/account/billing/basic.html')


@account_bp.route('/billing/enterprise')
@login_required
def billing_enterprise():
    """Enterprise billing"""
    return render_template('modules/account/billing/enterprise.html')


@account_bp.route('/billing/plans')
@login_required
def billing_plans():
    """Billing plans"""
    return render_template('modules/account/billing/plans.html')


@account_bp.route('/billing/history')
@login_required
def billing_history():
    """Billing history"""
    return render_template('modules/account/billing/history.html')


# Security Routes
@account_bp.route('/security/get-started')
@login_required
def security_get_started():
    """Security get started"""
    return render_template('modules/account/security/get_started.html')


@account_bp.route('/security/overview')
@login_required
def security_overview():
    """Security overview"""
    return render_template('modules/account/security/overview.html')


@account_bp.route('/security/allowed-ip-addresses')
@login_required
def security_allowed_ip():
    """Allowed IP addresses"""
    return render_template('modules/account/security/allowed_ip_addresses.html')


@account_bp.route('/security/privacy-settings')
@login_required
def security_privacy():
    """Privacy settings"""
    return render_template('modules/account/security/privacy_settings.html')


@account_bp.route('/security/device-management')
@login_required
def security_device_management():
    """Device management"""
    return render_template('modules/account/security/device_management.html')


@account_bp.route('/security/backup-and-recovery')
@login_required
def security_backup_recovery():
    """Backup and recovery"""
    return render_template('modules/account/security/backup_and_recovery.html')


@account_bp.route('/security/current-sessions')
@login_required
def security_current_sessions():
    """Current sessions"""
    return render_template('modules/account/security/current_sessions.html')


@account_bp.route('/security/security-log')
@login_required
def security_log():
    """Security log"""
    return render_template('modules/account/security/security_log.html')


# Members & Roles Routes
@account_bp.route('/members/teams')
@login_required
def members_teams():
    """Teams management"""
    return render_template('modules/account/members/teams.html')


@account_bp.route('/members/team-starter')
@login_required
def members_team_starter():
    """Team starter"""
    return render_template('modules/account/members/team_starter.html')


@account_bp.route('/members/team-members')
@login_required
def members_team_members():
    """Team members"""
    return render_template('modules/account/members/team_members.html')


@account_bp.route('/members/team-info')
@login_required
def members_team_info():
    """Team info"""
    return render_template('modules/account/members/team_info.html')


@account_bp.route('/members/roles')
@login_required
def members_roles():
    """Roles management"""
    return render_template('modules/account/members/roles.html')


@account_bp.route('/members/import-members')
@login_required
def members_import():
    """Import members"""
    return render_template('modules/account/members/import_members.html')


@account_bp.route('/members/permissions-check')
@login_required
def members_permissions_check():
    """Permissions check"""
    return render_template('modules/account/members/permissions_check.html')


@account_bp.route('/members/permissions-toggle')
@login_required
def members_permissions_toggle():
    """Permissions toggle"""
    return render_template('modules/account/members/permissions_toggle.html')


@account_bp.route('/members/members-starter')
@login_required
def members_members_starter():
    """Members starter"""
    return render_template('modules/account/members/members_starter.html')
