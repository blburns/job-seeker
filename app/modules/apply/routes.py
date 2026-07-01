"""Apply web routes - pre-fill review before submit."""

import logging
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import Application, ApplicationStage, ApplyDraft, MasterProfile, ResumeVersionStatus
from app.services.job_discovery_service import job_discovery_service
from app.services.resume_export_service import resume_export_service
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
        job = app_record.job_posting
        form_fields = job_discovery_service.build_apply_draft(
            profile.profile_data or {},
            {'title': job.title, 'company': job.company, 'url': job.url},
        )
        draft = ApplyDraft(
            application_id=app_record.id,
            user_id=current_user.id,
            form_fields=form_fields,
            status='draft',
        )
        db.session.add(draft)
        db.session.commit()

    version = app_record.resume_version
    keyword_analysis = None
    if app_record.job_posting and profile:
        from app.services.keyword_service import keyword_service
        jd_text = f"{app_record.job_posting.description or ''} {app_record.job_posting.requirements or ''}"
        keyword_analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})

    return render_template(
        'modules/apply/review.html',
        application=app_record,
        draft=draft,
        version=version,
        job=app_record.job_posting,
        keyword_analysis=keyword_analysis,
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
    draft.status = 'approved'
    db.session.commit()
    flash('Pre-fill draft saved.', 'success')
    return redirect(url_for('apply.review', application_id=application_id))


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
