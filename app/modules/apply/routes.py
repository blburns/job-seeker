"""Apply web routes - pre-fill review before submit."""

import logging
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import Application, ApplicationStage, ApplyDraft, MasterProfile, ResumeVersionStatus
from app.services.apply_draft_service import apply_draft_service
from app.services.activity_service import activity_service
from app.services.job_discovery_service import job_discovery_service
from app.services.resume_export_service import resume_export_service
from app.services.tailoring_service import tailoring_service
from app.services.credential_vault_service import credential_vault_service
from . import apply_bp

logger = logging.getLogger(__name__)


@apply_bp.route('/<uuid:application_id>')
@login_required
def review(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id
    ).order_by(ApplyDraft.created_at.desc()).first()

    if not draft and profile:
        draft = apply_draft_service.ensure_draft(app_record, current_user.id)
        if draft:
            db.session.commit()

    version = app_record.resume_version
    keyword_analysis = None
    resume_preview = ''
    if app_record.job_posting and profile:
        from app.services.keyword_service import keyword_service
        jd_text = f"{app_record.job_posting.description or ''} {app_record.job_posting.requirements or ''}"
        keyword_analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})
    if version:
        resume_preview = resume_export_service.render_preview_text(version.tailored_data or {})

    return render_template(
        'modules/apply/review.html',
        application=app_record,
        draft=draft,
        version=version,
        job=app_record.job_posting,
        keyword_analysis=keyword_analysis,
        resume_preview=resume_preview,
    )


@apply_bp.route('/<uuid:application_id>/save-draft', methods=['POST'])
@login_required
def save_draft(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id
    ).order_by(ApplyDraft.created_at.desc()).first_or_404()

    form_fields = dict(draft.form_fields or {})
    for key in form_fields:
        if key in request.form:
            form_fields[key] = request.form[key]
    draft.form_fields = form_fields
    if 'cover_letter' in request.form:
        draft.cover_letter = request.form['cover_letter']
    draft.status = 'approved'
    db.session.commit()
    flash('Pre-fill draft saved.', 'success')
    return redirect(url_for('apply.review', application_id=application_id))


@apply_bp.route('/<uuid:application_id>/regenerate-cover-letter', methods=['POST'])
@login_required
def regenerate_cover_letter(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    if not profile:
        flash('Upload a master profile first.', 'warning')
        return redirect(url_for('apply.review', application_id=application_id))

    profile_data = (app_record.resume_version.tailored_data if app_record.resume_version else None) or profile.profile_data or {}
    apply_draft_service.ensure_draft(
        app_record,
        current_user.id,
        profile_data=profile_data,
        regenerate_cover_letter=True,
    )
    db.session.commit()
    flash('Cover letter regenerated.', 'success')
    return redirect(request.referrer or url_for('apply.review', application_id=application_id))


@apply_bp.route('/<uuid:application_id>/download-cover-letter')
@login_required
def download_cover_letter(application_id):
    import io
    from flask import send_file

    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id
    ).order_by(ApplyDraft.created_at.desc()).first()
    if not draft or not (draft.cover_letter or '').strip():
        flash('No cover letter available. Tailor the resume or regenerate the letter.', 'warning')
        return redirect(url_for('apply.review', application_id=application_id))

    fmt = request.args.get('format', 'docx')
    job = app_record.job_posting
    base = f"Cover_Letter_{job.company}_{job.title}".replace(' ', '_')[:80] if job else 'Cover_Letter'
    if fmt == 'txt':
        return send_file(
            io.BytesIO(draft.cover_letter.encode('utf-8')),
            as_attachment=True,
            download_name=f'{base}.txt',
            mimetype='text/plain',
        )
    docx_bytes, filename = resume_export_service.export_cover_letter_docx(
        draft.cover_letter, f'{base}.docx',
    )
    return send_file(
        io.BytesIO(docx_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@apply_bp.route('/<uuid:application_id>/mark-applied', methods=['POST'])
@login_required
def mark_applied(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    if app_record.stage not in (ApplicationStage.READY_TO_APPLY.value, ApplicationStage.TAILORING.value):
        if not app_record.resume_version or app_record.resume_version.status != ResumeVersionStatus.APPROVED.value:
            flash('Approve tailored resume before marking as applied.', 'warning')
            return redirect(url_for('apply.review', application_id=application_id))

    app_record.stage = ApplicationStage.APPLIED.value
    app_record.applied_at = datetime.utcnow()
    if app_record.resume_version and app_record.resume_version.keyword_coverage:
        app_record.keyword_coverage_at_apply = app_record.resume_version.keyword_coverage
    activity_service.log(app_record.id, current_user.id, 'submit', subject='Marked applied manually')
    db.session.commit()
    flash('Marked as applied.', 'success')
    return redirect(url_for('applications.detail', application_id=application_id))


@apply_bp.route('/<uuid:application_id>/download-resume')
@login_required
def download_resume(application_id):
    import io
    from flask import send_file

    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    version = app_record.resume_version
    if not version or not version.tailored_data:
        flash('No tailored resume available.', 'warning')
        return redirect(url_for('apply.review', application_id=application_id))

    docx_bytes, filename = resume_export_service.export_docx(version.tailored_data)
    return send_file(
        io.BytesIO(docx_bytes),
        as_attachment=True,
        download_name=version.export_filename or filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@apply_bp.route('/credentials')
@login_required
def credentials_list():
    creds = credential_vault_service.list_credentials(current_user.id)
    active_portals = {
        portal: credential_vault_service.has_active(current_user.id, portal)
        for portal in ('linkedin', 'indeed', 'greenhouse', 'lever')
    }
    return render_template(
        'modules/apply/credentials.html',
        credentials=creds,
        active_portals=active_portals,
        encryption_key_configured=credential_vault_service.encryption_key_configured(),
    )


@apply_bp.route('/credentials/<portal>/test', methods=['POST'])
@login_required
def credentials_test(portal):
    from app.services.scraping.session_health import session_health
    result = session_health.check_and_update_credential(current_user.id, portal)
    if result.ok:
        flash(f'{portal.title()} session is valid.', 'success')
    else:
        flash(f'{portal.title()} session check failed: {result.message}', 'danger')
    return redirect(url_for('apply.credentials_list'))


@apply_bp.route('/credentials/<uuid:credential_id>/delete', methods=['POST'])
@login_required
def credentials_delete(credential_id):
    if credential_vault_service.delete(current_user.id, credential_id):
        flash('Credential deleted.', 'success')
    else:
        flash('Credential not found.', 'warning')
    return redirect(url_for('apply.credentials_list'))


@apply_bp.route('/credentials/<portal>/clear', methods=['POST'])
@login_required
def credentials_clear_portal(portal):
    count = credential_vault_service.delete_for_portal(current_user.id, portal)
    if count:
        flash(f'Deleted {count} {portal.title()} credential(s).', 'success')
    else:
        flash(f'No {portal.title()} credentials to delete.', 'info')
    return redirect(url_for('apply.credentials_list'))


@apply_bp.route('/credentials', methods=['POST'])
@login_required
def credentials_store():
    portal = request.form.get('portal', '').strip()
    session_data = request.form.get('session_data', '').strip()
    label = request.form.get('label', '').strip()
    if not portal or not session_data:
        flash('Portal and session data are required.', 'warning')
        return redirect(url_for('apply.credentials_list'))
    try:
        import json
        data = json.loads(session_data)
    except json.JSONDecodeError:
        flash('Session data must be valid JSON (paste the full storage_state export file).', 'danger')
        return redirect(url_for('apply.credentials_list'))
    try:
        data = credential_vault_service.validate_portal_data(portal, data)
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('apply.credentials_list'))
    if not credential_vault_service.encryption_key_configured():
        flash(
            'Warning: CREDENTIAL_ENCRYPTION_KEY is not set in .env — credentials may not survive an app restart.',
            'warning',
        )
    credential_vault_service.store(current_user.id, portal, data, label=label)
    flash(f'{portal.title()} credentials stored securely.', 'success')
    return redirect(url_for('apply.credentials_list'))
