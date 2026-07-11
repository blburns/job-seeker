"""
Admin Routes
Administrative interface for RBAC management
"""

import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions.core import db
from app.modules.admin import admin_bp
from app.models.auth import Role, User, Group
from app.models.rbac import Permission, UserRoleAssignment, RoleHierarchy
from app.services.rbac_service import rbac_service
from app.services.admin_service import admin_service
from app.utils.rbac_decorators import admin_required, permission_required

logger = logging.getLogger(__name__)


# ============================================================================
# Dashboard
# ============================================================================

def _default_rbac_stats():
    """Default RBAC stats when query fails (e.g. after a failed transaction)."""
    return {
        'total_permissions': 0,
        'active_permissions': 0,
        'total_roles': 0,
        'active_roles': 0,
        'total_assignments': 0,
        'active_assignments': 0,
        'expired_assignments': 0,
        'role_hierarchies': 0,
    }


def _empty_dashboard_summary():
    """Empty dashboard summary for fast initial render (data loaded via AJAX)."""
    return {
        'users': {
            'total': 0,
            'active': 0,
            '2fa_percentage': 0,
            'verified': 0,
            'with_2fa': 0,
            'admins': 0,
        },
        'sessions': {
            'active': 0,
            'total': 0,
            'by_device': {},
        },
        'signups': {
            'total': 0,
            'average_daily': 0,
        },
        'emails': {
            'sent': 0,
            'success_rate': 0,
            'failed': 0,
        },
        'system_health': {
            'database': {'status': 'unknown', 'message': 'Loading…'},
            'redis': {'status': 'unknown', 'message': 'Loading…'},
            'celery': {'status': 'unknown', 'message': 'Loading…'},
            'disk': {'status': 'unknown', 'message': 'Loading…'},
        },
        'recent_logins': [],
        'recent_actions': [],
        'timestamp': None,
    }


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required()
def dashboard():
    """Admin dashboard shell; data is loaded via AJAX for fast initial render."""
    try:
        db.session.rollback()
        return render_template(
            'modules/admin/dashboard.html',
            summary=_empty_dashboard_summary(),
            rbac_stats=_default_rbac_stats(),
            growth_data=[],
        )
    except Exception as e:
        logger.exception('Error in admin dashboard')
        db.session.rollback()
        flash('An error occurred loading the dashboard', 'danger')
        return redirect(url_for('main.index'))


@admin_bp.route('/api/dashboard/data')
@login_required
@admin_required(api_mode=True)
def api_dashboard_data():
    """API: Full dashboard data (summary, rbac_stats, growth_data) for AJAX load."""
    try:
        db.session.rollback()
        summary = admin_service.get_dashboard_summary()
        try:
            rbac_stats = rbac_service.get_statistics()
        except Exception:
            logger.exception('Error getting RBAC statistics')
            db.session.rollback()
            rbac_stats = _default_rbac_stats()
        try:
            growth_data = admin_service.get_user_growth_data(months=6)
        except Exception:
            logger.exception('Error getting user growth data')
            db.session.rollback()
            growth_data = []
        return jsonify({
            'summary': summary,
            'rbac_stats': rbac_stats,
            'growth_data': growth_data,
        })
    except Exception as e:
        logger.exception('Error in API dashboard data')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# User Management (Redirects/Aliases)
# ============================================================================

@admin_bp.route('/users')
@login_required
@admin_required()
def users_redirect():
    """Redirect to users list (alias for /users/list)"""
    return redirect(url_for('users.list_users'))


# ============================================================================
# Permission Management
# ============================================================================

@admin_bp.route('/permissions')
@login_required
@permission_required('permissions.view')
def permissions_list():
    """List all permissions grouped by module with summary stats."""
    try:
        grouped = rbac_service.get_permissions_grouped_by_module(active_only=False)
        grouped_permissions = dict(sorted(grouped.items(), key=lambda t: (t[0].lower())))
        try:
            rbac_stats = rbac_service.get_statistics()
        except Exception:
            rbac_stats = {}
        return render_template(
            'modules/admin/permissions/list.html',
            grouped_permissions=grouped_permissions,
            rbac_stats=rbac_stats,
        )
    except Exception:
        logger.exception('Error listing permissions')
        flash('An error occurred loading permissions', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/permissions/create', methods=['GET', 'POST'])
@login_required
@permission_required('permissions.manage')
def permission_create():
    """Create a new permission"""
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            display_name = request.form.get('display_name')
            module = request.form.get('module')
            description = request.form.get('description')
            category = request.form.get('category')
            priority = int(request.form.get('priority', 0))
            
            if not name or not display_name or not module:
                flash('Name, display name, and module are required', 'warning')
                return render_template('modules/admin/permissions/create.html')
            
            permission = rbac_service.create_permission(
                name=name,
                display_name=display_name,
                module=module,
                description=description,
                category=category,
                priority=priority
            )
            
            flash(f'Permission "{display_name}" created successfully', 'success')
            return redirect(url_for('admin.permissions_list'))
        
        return render_template('modules/admin/permissions/create.html')
    except Exception as e:
        logger.exception('Error creating permission')
        db.session.rollback()
        flash('An error occurred creating the permission', 'danger')
        return redirect(url_for('admin.permissions_list'))


@admin_bp.route('/permissions/<permission_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('permissions.manage')
def permission_edit(permission_id):
    """Edit a permission"""
    try:
        permission = Permission.query.get_or_404(permission_id)
        
        if request.method == 'POST':
            permission.display_name = request.form.get('display_name')
            permission.description = request.form.get('description')
            permission.category = request.form.get('category')
            permission.priority = int(request.form.get('priority', 0))
            permission.is_active = request.form.get('is_active') == '1'
            permission.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Permission "{permission.display_name}" updated successfully', 'success')
            return redirect(url_for('admin.permissions_list'))
        
        roles_with_permission = list(permission.roles) if permission.roles else []
        return render_template(
            'modules/admin/permissions/edit.html',
            permission=permission,
            roles_with_permission=roles_with_permission,
        )
    except Exception:
        logger.exception('Error editing permission')
        db.session.rollback()
        flash('An error occurred updating the permission', 'danger')
        return redirect(url_for('admin.permissions_list'))


@admin_bp.route('/permissions/<permission_id>/delete', methods=['POST'])
@login_required
@permission_required('permissions.manage')
def permission_delete(permission_id):
    """Delete a permission"""
    try:
        permission = Permission.query.get_or_404(permission_id)
        
        if permission.is_system:
            flash('Cannot delete system permission', 'danger')
            return redirect(url_for('admin.permissions_list'))
        
        name = permission.display_name
        db.session.delete(permission)
        db.session.commit()
        
        flash(f'Permission "{name}" deleted successfully', 'success')
        return redirect(url_for('admin.permissions_list'))
    except Exception as e:
        logger.exception('Error deleting permission')
        db.session.rollback()
        flash('An error occurred deleting the permission', 'danger')
        return redirect(url_for('admin.permissions_list'))


# ============================================================================
# Role Management
# ============================================================================

@admin_bp.route('/roles')
@login_required
@permission_required('roles.view')
def roles_list():
    """List all roles with summary stats and assignment counts."""
    try:
        roles = rbac_service.get_all_roles(active_only=False)
        try:
            rbac_stats = rbac_service.get_statistics()
            role_assignment_counts = rbac_service.get_role_assignment_counts()
        except Exception:
            rbac_stats = {}
            role_assignment_counts = {}
        return render_template(
            'modules/admin/roles/list.html',
            roles=roles,
            rbac_stats=rbac_stats,
            role_assignment_counts=role_assignment_counts,
        )
    except Exception:
        logger.exception('Error listing roles')
        flash('An error occurred loading roles', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/roles/create', methods=['GET', 'POST'])
@login_required
@permission_required('roles.create')
def role_create():
    """Create a new role"""
    try:
        if request.method == 'POST':
            name = request.form.get('name')
            display_name = request.form.get('display_name')
            description = request.form.get('description')
            priority = int(request.form.get('priority', 0))
            
            if not name or not display_name:
                flash('Name and display name are required', 'warning')
                return render_template('modules/admin/roles/create.html')
            
            role = rbac_service.create_role(
                name=name,
                display_name=display_name,
                description=description,
                priority=priority
            )
            
            flash(f'Role "{display_name}" created successfully', 'success')
            return redirect(url_for('admin.role_edit', role_id=role.id))
        
        return render_template('modules/admin/roles/create.html')
    except Exception as e:
        logger.exception('Error creating role')
        db.session.rollback()
        flash('An error occurred creating the role', 'danger')
        return redirect(url_for('admin.roles_list'))


@admin_bp.route('/roles/<role_id>')
@login_required
@permission_required('roles.view')
def role_view(role_id):
    """View role details"""
    try:
        role = Role.query.get_or_404(role_id)
        permissions = rbac_service.get_role_permissions(role_id)
        assignments = rbac_service.get_role_users(role_id)
        hierarchy = rbac_service.get_role_hierarchy(role_id)
        
        return render_template('modules/admin/roles/view.html',
                             role=role,
                             permissions=permissions,
                             assignments=assignments,
                             hierarchy=hierarchy)
    except Exception as e:
        logger.exception('Error viewing role')
        flash('An error occurred loading the role', 'danger')
        return redirect(url_for('admin.roles_list'))


@admin_bp.route('/roles/<role_id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('roles.update')
def role_edit(role_id):
    """Edit a role"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if request.method == 'POST':
            role.display_name = request.form.get('display_name')
            role.description = request.form.get('description')
            role.priority = int(request.form.get('priority', 0))
            role.is_active = request.form.get('is_active') == '1'
            role.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Role "{role.display_name}" updated successfully', 'success')
            return redirect(url_for('admin.role_view', role_id=role.id))
        
        return render_template('modules/admin/roles/edit.html', role=role)
    except Exception as e:
        logger.exception('Error editing role')
        db.session.rollback()
        flash('An error occurred updating the role', 'danger')
        return redirect(url_for('admin.roles_list'))


@admin_bp.route('/roles/<role_id>/permissions', methods=['GET', 'POST'])
@login_required
@permission_required('roles.update')
def role_permissions(role_id):
    """Manage role permissions"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if request.method == 'POST':
            # Get selected permission IDs from form
            permission_ids = request.form.getlist('permissions')
            
            # Sync permissions
            rbac_service.sync_role_permissions(role_id, permission_ids)
            
            flash(f'Permissions updated for role "{role.display_name}"', 'success')
            return redirect(url_for('admin.role_view', role_id=role.id))
        
        # Get all permissions grouped by module
        grouped_permissions = rbac_service.get_permissions_grouped_by_module()
        
        # Get current role permissions
        current_permissions = rbac_service.get_role_permissions(role_id)
        current_permission_ids = [str(p.id) for p in current_permissions]
        
        return render_template('modules/admin/roles/permissions.html',
                             role=role,
                             grouped_permissions=grouped_permissions,
                             current_permission_ids=current_permission_ids)
    except Exception as e:
        logger.exception('Error managing role permissions')
        db.session.rollback()
        flash('An error occurred updating permissions', 'danger')
        return redirect(url_for('admin.role_view', role_id=role_id))


@admin_bp.route('/roles/<role_id>/delete', methods=['POST'])
@login_required
@permission_required('roles.delete')
def role_delete(role_id):
    """Delete a role"""
    try:
        role = Role.query.get_or_404(role_id)
        
        if role.is_system_role:
            flash('Cannot delete system role', 'danger')
            return redirect(url_for('admin.roles_list'))
        
        name = role.display_name
        db.session.delete(role)
        db.session.commit()
        
        flash(f'Role "{name}" deleted successfully', 'success')
        return redirect(url_for('admin.roles_list'))
    except Exception as e:
        logger.exception('Error deleting role')
        db.session.rollback()
        flash('An error occurred deleting the role', 'danger')
        return redirect(url_for('admin.roles_list'))


# ============================================================================
# User Role Assignment
# ============================================================================

@admin_bp.route('/users/<user_id>/roles')
@login_required
@permission_required('roles.assign')
def user_roles(user_id):
    """Manage user roles"""
    try:
        user = User.query.get_or_404(user_id)
        assignments = rbac_service.get_user_roles(user_id, active_only=False)
        available_roles = rbac_service.get_all_roles()
        
        return render_template('modules/admin/users/roles.html',
                             user=user,
                             assignments=assignments,
                             available_roles=available_roles)
    except Exception as e:
        logger.exception('Error viewing user roles')
        flash('An error occurred loading user roles', 'danger')
        return redirect(url_for('users.view', user_id=user_id))


@admin_bp.route('/users/<user_id>/roles/assign', methods=['POST'])
@login_required
@permission_required('roles.assign')
def user_role_assign(user_id):
    """Assign a role to a user"""
    try:
        user = User.query.get_or_404(user_id)
        role_id = request.form.get('role_id')
        expires_days = request.form.get('expires_days')
        notes = request.form.get('notes')
        
        if not role_id:
            flash('Please select a role', 'warning')
            return redirect(url_for('admin.user_roles', user_id=user_id))
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            try:
                days = int(expires_days)
                if days > 0:
                    expires_at = datetime.utcnow() + timedelta(days=days)
            except ValueError:
                pass
        
        # Assign role
        rbac_service.assign_role_to_user(
            user_id=user_id,
            role_id=role_id,
            assigned_by_id=str(current_user.id),
            expires_at=expires_at,
            notes=notes
        )
        
        role = Role.query.get(role_id)
        flash(f'Role "{role.display_name}" assigned to {user.username}', 'success')
        return redirect(url_for('admin.user_roles', user_id=user_id))
    except ValueError as e:
        flash(str(e), 'warning')
        return redirect(url_for('admin.user_roles', user_id=user_id))
    except Exception as e:
        logger.exception('Error assigning role to user')
        db.session.rollback()
        flash('An error occurred assigning the role', 'danger')
        return redirect(url_for('admin.user_roles', user_id=user_id))


@admin_bp.route('/users/<user_id>/roles/<role_id>/revoke', methods=['POST'])
@login_required
@permission_required('roles.assign')
def user_role_revoke(user_id, role_id):
    """Revoke a role from a user"""
    try:
        user = User.query.get_or_404(user_id)
        role = Role.query.get_or_404(role_id)
        reason = request.form.get('reason')
        
        rbac_service.revoke_role_from_user(
            user_id=user_id,
            role_id=role_id,
            revoked_by_id=str(current_user.id),
            reason=reason
        )
        
        flash(f'Role "{role.display_name}" revoked from {user.username}', 'success')
        return redirect(url_for('admin.user_roles', user_id=user_id))
    except Exception as e:
        logger.exception('Error revoking role from user')
        db.session.rollback()
        flash('An error occurred revoking the role', 'danger')
        return redirect(url_for('admin.user_roles', user_id=user_id))


# ============================================================================
# API Endpoints
# ============================================================================

@admin_bp.route('/api/permissions')
@login_required
@permission_required('permissions.view', api_mode=True)
def api_permissions():
    """API: Get all permissions"""
    try:
        permissions = rbac_service.get_all_permissions()
        return jsonify({
            'permissions': [p.to_dict() for p in permissions]
        })
    except Exception as e:
        logger.exception('Error in API permissions')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/roles')
@login_required
@permission_required('roles.view', api_mode=True)
def api_roles():
    """API: Get all roles"""
    try:
        roles = rbac_service.get_all_roles()
        return jsonify({
            'roles': [r.to_dict() for r in roles]
        })
    except Exception as e:
        logger.exception('Error in API roles')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/roles/<role_id>/permissions')
@login_required
@permission_required('roles.view', api_mode=True)
def api_role_permissions(role_id):
    """API: Get role permissions"""
    try:
        permissions = rbac_service.get_role_permissions(role_id)
        return jsonify({
            'permissions': [p.to_dict() for p in permissions]
        })
    except Exception as e:
        logger.exception('Error in API role permissions')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/users/<user_id>/permissions')
@login_required
@permission_required('users.view', api_mode=True)
def api_user_permissions(user_id):
    """API: Get user permissions"""
    try:
        permissions = rbac_service.get_user_all_permissions(user_id)
        return jsonify({
            'permissions': permissions
        })
    except Exception as e:
        logger.exception('Error in API user permissions')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/stats')
@login_required
@admin_required(api_mode=True)
def api_stats():
    """API: Get RBAC statistics"""
    try:
        stats = rbac_service.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.exception('Error in API stats')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# System Monitoring
# ============================================================================

def _empty_monitoring_context():
    """Empty monitoring context so the template renders; data can be loaded via AJAX or full reload."""
    return {
        'system_health': {
            'database': {'status': 'unknown', 'message': 'Loading…', 'size_mb': None},
            'redis': {'status': 'unknown', 'message': 'Loading…', 'version': None, 'used_memory_mb': None},
            'celery': {'status': 'unknown', 'message': 'Loading…', 'workers': 0, 'active_tasks': 0},
            'disk': {'status': 'unknown', 'message': 'Loading…', 'free_gb': None, 'total_gb': None},
        },
        'user_metrics': {
            'total': 0, 'active': 0, 'verified': 0, 'admins': 0,
            'with_2fa': 0, '2fa_percentage': 0,
        },
        'session_metrics': {
            'active': 0, 'total': 0, 'expired': 0, 'by_device': {},
        },
        'email_metrics': {
            'total': 0, 'sent': 0, 'delivered': 0, 'failed': 0, 'bounced': 0, 'success_rate': 0,
        },
        'signup_metrics': {
            'total': 0, 'period_days': 30, 'average_daily': 0,
        },
        'recent_logins': [],
        'failed_logins': [],
        'recent_actions': [],
    }


@admin_bp.route('/monitoring')
@login_required
@admin_required()
def monitoring():
    """Monitoring page: render immediately with empty context; data loaded via AJAX (same pattern as dashboard)."""
    try:
        db.session.rollback()
        return render_template('modules/admin/monitoring.html', **_empty_monitoring_context())
    except Exception as e:
        logger.exception('Error in monitoring dashboard')
        db.session.rollback()
        flash('An error occurred loading the monitoring dashboard', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api/monitoring/data')
@login_required
@admin_required(api_mode=True)
def api_monitoring_data():
    """API: Full monitoring data for AJAX load."""
    try:
        db.session.rollback()
        system_health = admin_service.get_system_health()
        user_metrics = admin_service.get_user_metrics()
        session_metrics = admin_service.get_session_metrics()
        email_metrics = admin_service.get_email_metrics(days=7)
        signup_metrics = admin_service.get_signup_metrics(days=30)
        recent_logins = admin_service.get_recent_logins(limit=20)
        failed_logins = admin_service.get_failed_login_attempts(hours=24)
        recent_actions = admin_service.get_recent_user_actions(limit=20)
        return jsonify({
            'system_health': system_health,
            'user_metrics': user_metrics,
            'session_metrics': session_metrics,
            'email_metrics': email_metrics,
            'signup_metrics': signup_metrics,
            'recent_logins': recent_logins,
            'failed_logins': failed_logins,
            'recent_actions': recent_actions,
        })
    except Exception as e:
        logger.exception('Error in API monitoring data')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/monitoring/health')
@login_required
@admin_required(api_mode=True)
def api_monitoring_health():
    """API: Get system health status"""
    try:
        health = admin_service.get_system_health()
        return jsonify(health)
    except Exception as e:
        logger.exception('Error in API monitoring health')
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/monitoring/metrics')
@login_required
@admin_required(api_mode=True)
def api_monitoring_metrics():
    """API: Get all monitoring metrics"""
    try:
        metrics = {
            'users': admin_service.get_user_metrics(),
            'sessions': admin_service.get_session_metrics(),
            'emails': admin_service.get_email_metrics(days=7),
            'signups': admin_service.get_signup_metrics(days=30)
        }
        return jsonify(metrics)
    except Exception as e:
        logger.exception('Error in API monitoring metrics')
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Communications (Email)
# ============================================================================

@admin_bp.route('/email/logs')
@login_required
@admin_required()
def email_logs():
    """View email logs – paginated list with status and period filters."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        status_filter = request.args.get('status', '').strip() or None
        days = request.args.get('days', '', type=str).strip()
        days = int(days) if days.isdigit() else None
        data = admin_service.get_email_logs_list(
            page=page,
            per_page=per_page,
            status=status_filter,
            days=days,
        )
        return render_template(
            'modules/admin/email/logs.html',
            items=data.get('items', []),
            pagination={
                'total': data.get('total', 0),
                'page': data.get('page', 1),
                'per_page': data.get('per_page', 25),
                'total_pages': data.get('total_pages', 0),
                'has_next': data.get('has_next', False),
                'has_prev': data.get('has_prev', False),
            },
            summary=data.get('summary', {}),
            days_filter=data.get('days_filter'),
            status_filter=data.get('status_filter') or '',
        )
    except Exception:
        logger.exception('Error loading email logs')
        db.session.rollback()
        flash('An error occurred loading email logs', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/email/templates')
@login_required
@admin_required()
def email_templates():
    """List email templates (files under app/templates/emails/) with usage stats."""
    try:
        template_list = admin_service.get_email_template_list(current_app)
        return render_template(
            'modules/admin/email/templates.html',
            template_list=template_list,
        )
    except Exception:
        logger.exception('Error loading email templates')
        db.session.rollback()
        flash('An error occurred loading email templates', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/proofs')
@login_required
@admin_required()
def proofs_list():
    """Browse scrape and submission proof screenshots."""
    from app.services.proof_paths import list_proof_files

    kind = (request.args.get('kind') or 'all').strip().lower()
    if kind not in ('all', 'scrape', 'submission'):
        kind = 'all'
    proofs = list_proof_files(kind=kind, limit=200)
    return render_template(
        'modules/admin/proofs.html',
        proofs=proofs,
        kind=kind,
    )


@admin_bp.route('/proofs/file')
@login_required
@admin_required()
def proofs_file():
    """Serve a proof PNG only if it lives under an allowed proof directory."""
    from flask import abort, send_file
    from app.services.proof_paths import resolve_safe_proof_path

    stored = (request.args.get('path') or '').strip()
    path = resolve_safe_proof_path(stored)
    if not path:
        abort(404)
    return send_file(path, mimetype='image/png')


@admin_bp.route('/email/templates/<name>/preview')
@login_required
@admin_required()
def email_template_preview(name):
    """Preview an email template with sample context (no real user data)."""
    try:
        template_list = admin_service.get_email_template_list(current_app)
        allowed = {t['name'] for t in template_list}
        if not name or name.strip() not in allowed:
            flash('Template not found or access denied', 'danger')
            return redirect(url_for('admin.email_templates'))
        name = name.strip()
        context = admin_service.get_email_template_preview_context(current_app)
        return render_template(f'emails/{name}.html', **context)
    except Exception:
        logger.exception('Error previewing email template')
        flash('An error occurred previewing the template', 'danger')
        return redirect(url_for('admin.email_templates'))


@admin_bp.route('/email/templates/create', methods=['GET', 'POST'])
@login_required
@admin_required()
def email_template_create():
    """Create a new email template (writes to app/templates/emails/<name>.html)."""
    try:
        if request.method == 'POST':
            name = (request.form.get('name') or '').strip().lower()
            content = request.form.get('content') or ''
            if not name:
                flash('Template name is required.', 'warning')
                return render_template(
                    'modules/admin/email/template_form.html',
                    template_name='',
                    content=content,
                    is_edit=False,
                )
            if not admin_service._EMAIL_TEMPLATE_NAME_RE.match(name):
                flash('Name must be lowercase letters, numbers, and underscores only (e.g. my_template).', 'warning')
                return render_template(
                    'modules/admin/email/template_form.html',
                    template_name=name,
                    content=content,
                    is_edit=False,
                )
            if admin_service.email_template_exists(current_app, name):
                flash(f'A template named "{name}" already exists. Choose another name or edit it.', 'warning')
                return render_template(
                    'modules/admin/email/template_form.html',
                    template_name=name,
                    content=content,
                    is_edit=False,
                )
            if admin_service.write_email_template_content(current_app, name, content):
                flash(f'Template "{name}" created successfully.', 'success')
                return redirect(url_for('admin.email_templates'))
            flash('Failed to create template file.', 'danger')
            return redirect(url_for('admin.email_template_create'))
        return render_template(
            'modules/admin/email/template_form.html',
            template_name='',
            content='',
            is_edit=False,
        )
    except Exception:
        logger.exception('Error creating email template')
        flash('An error occurred creating the template.', 'danger')
        return redirect(url_for('admin.email_templates'))


@admin_bp.route('/email/templates/<name>/edit', methods=['GET', 'POST'])
@login_required
@admin_required()
def email_template_edit(name):
    """Edit an existing email template."""
    try:
        template_list = admin_service.get_email_template_list(current_app)
        allowed = {t['name'] for t in template_list}
        if not name or name.strip() not in allowed:
            flash('Template not found or access denied.', 'danger')
            return redirect(url_for('admin.email_templates'))
        name = name.strip()
        if request.method == 'POST':
            content = request.form.get('content') or ''
            if admin_service.write_email_template_content(current_app, name, content):
                flash(f'Template "{name}" updated successfully.', 'success')
                return redirect(url_for('admin.email_templates'))
            flash('Failed to save template.', 'danger')
            return redirect(url_for('admin.email_template_edit', name=name))
        content = admin_service.read_email_template_content(current_app, name)
        if content is None:
            flash('Could not read template content.', 'danger')
            return redirect(url_for('admin.email_templates'))
        return render_template(
            'modules/admin/email/template_form.html',
            template_name=name,
            content=content,
            is_edit=True,
        )
    except Exception:
        logger.exception('Error editing email template')
        flash('An error occurred editing the template.', 'danger')
        return redirect(url_for('admin.email_templates'))


# ============================================================================
# System Settings
# ============================================================================

@admin_bp.route('/settings')
@login_required
@admin_required()
def system_settings():
    """System settings – read-only view of application config (from env)."""
    try:
        settings_sections = admin_service.get_settings_display_config(current_app)
        return render_template(
            'modules/admin/settings.html',
            settings_sections=settings_sections,
        )
    except Exception:
        logger.exception('Error loading system settings')
        db.session.rollback()
        flash('An error occurred loading settings', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/logs')
@login_required
@admin_required()
def system_logs():
    """View system logs – tail of selected log file from app/data/logs/."""
    try:
        file_param = request.args.get('file', 'app', type=str).strip().lower() or 'app'
        allowed = {t[0] for t in admin_service.ALLOWED_LOG_FILES}
        if file_param not in allowed:
            file_param = 'app'
        lines = request.args.get('lines', 200, type=int)
        level_filter = request.args.get('level', '').strip() or None
        log_data = admin_service.get_log_tail(
            current_app, log_name=file_param, lines=lines, level_filter=level_filter
        )
        return render_template(
            'modules/admin/logs.html',
            log_file=log_data.get('log_file'),
            log_file_name=file_param,
            allowed_log_files=admin_service.ALLOWED_LOG_FILES,
            entries=log_data.get('entries', []),
            total_read=log_data.get('total_read', 0),
            log_error=log_data.get('error'),
            lines_param=min(max(1, lines), admin_service._MAX_TAIL_LINES),
            level_filter=level_filter or '',
        )
    except Exception:
        logger.exception('Error loading system logs')
        db.session.rollback()
        flash('An error occurred loading logs', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/api/logs')
@login_required
@admin_required(api_mode=True)
def api_logs():
    """API: Tail of log file for AJAX (file, lines, level query params)."""
    try:
        file_param = request.args.get('file', 'app', type=str).strip().lower() or 'app'
        allowed = {t[0] for t in admin_service.ALLOWED_LOG_FILES}
        if file_param not in allowed:
            file_param = 'app'
        lines = request.args.get('lines', 200, type=int)
        level_filter = request.args.get('level', '').strip() or None
        log_data = admin_service.get_log_tail(
            current_app, log_name=file_param, lines=lines, level_filter=level_filter
        )
        return jsonify({
            'log_file': log_data.get('log_file'),
            'entries': log_data.get('entries', []),
            'total_read': log_data.get('total_read', 0),
            'error': log_data.get('error'),
        })
    except Exception as err:
        logger.exception('Error in API logs')
        db.session.rollback()
        return jsonify({'error': str(err)}), 500


# ============================================================================
# Analytics & Reports
# ============================================================================

@admin_bp.route('/reports')
@login_required
@admin_required()
def reports():
    """View reports – user activity, sessions, email, security, RBAC."""
    try:
        period = request.args.get('period', 30, type=int)
        if period not in (7, 30, 90):
            period = 30
        report_data = admin_service.get_reports_data(period_days=period)
        return render_template(
            'modules/admin/reports.html',
            report=report_data,
            period=period,
        )
    except Exception:
        logger.exception('Error loading reports')
        db.session.rollback()
        flash('An error occurred loading reports', 'danger')
        return redirect(url_for('admin.dashboard'))


# ============================================================================
# Developer Tools
# ============================================================================

@admin_bp.route('/developer/sitemap')
@login_required
@admin_required()
def developer_sitemap():
    """Developer Sitemap - List all registered routes"""
    from flask import current_app
    
    routes = []
    for rule in current_app.url_map.iter_rules():
        # Skip static files
        if rule.endpoint == 'static':
            continue
            
        # Get methods (excluding HEAD, OPTIONS)
        methods = [m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
        
        # Get view function docstring
        view_func = current_app.view_functions.get(rule.endpoint)
        docstring = view_func.__doc__ if view_func and view_func.__doc__ else 'No description available'
        
        # Determine blueprint
        parts = rule.endpoint.split('.')
        blueprint = parts[0] if len(parts) > 1 else 'app'
        
        routes.append({
            'rule': str(rule),
            'methods': ', '.join(sorted(methods)),
            'endpoint': rule.endpoint,
            'blueprint': blueprint,
            'description': docstring.strip().split('\n')[0] if docstring else ''
        })
    
    # Sort by blueprint then rule
    routes.sort(key=lambda x: (x['blueprint'], x['rule']))

    # Group by blueprint (sorted by blueprint name for consistent display)
    grouped = {}
    for route in routes:
        bp = route['blueprint']
        if bp not in grouped:
            grouped[bp] = []
        grouped[bp].append(route)
    grouped_routes = dict(sorted(grouped.items(), key=lambda t: t[0].lower()))

    total_routes = sum(len(r) for r in grouped_routes.values())
    return render_template(
        'modules/admin/developer/sitemap.html',
        grouped_routes=grouped_routes,
        total_routes=total_routes,
    )
