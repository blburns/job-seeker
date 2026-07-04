"""Apply API routes."""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import Application, ApplicationStage, ApplyBatch, ApplyBatchItem, ApplyDraft, MasterProfile
from app.services.apply_batch_service import apply_batch_service
from app.services.activity_service import activity_service
from app.services.job_discovery_service import job_discovery_service

logger = logging.getLogger(__name__)

apply_api_bp = Blueprint('apply_api', __name__, url_prefix='/api/v1/apply')


@apply_api_bp.route('/drafts/<uuid:application_id>', methods=['GET'])
@login_required
def get_draft(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id
    ).order_by(ApplyDraft.created_at.desc()).first()
    if not draft:
        return jsonify({'error': 'No draft found'}), 404
    return jsonify(draft.to_dict())


@apply_api_bp.route('/drafts/<uuid:application_id>', methods=['POST'])
@login_required
def create_draft(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    if not profile:
        return jsonify({'error': 'No active master profile'}), 400

    job = app_record.job_posting
    form_fields = job_discovery_service.build_apply_draft(
        profile.profile_data or {},
        {
            'title': job.title,
            'company': job.company,
            'url': job.url,
        },
    )
    from app.services.tailoring_service import tailoring_service
    cover_letter = tailoring_service.generate_cover_letter_for_job(
        profile.profile_data or {},
        job.title,
        job.company,
        f"{job.description or ''} {job.requirements or ''}",
    )
    draft = ApplyDraft(
        application_id=app_record.id,
        user_id=current_user.id,
        form_fields=form_fields,
        cover_letter=cover_letter,
        status='draft',
    )
    db.session.add(draft)
    db.session.commit()
    return jsonify(draft.to_dict()), 201


@apply_api_bp.route('/drafts/<uuid:draft_id>/approve', methods=['POST'])
@login_required
def approve_draft(draft_id):
    draft = ApplyDraft.query.filter_by(id=draft_id, user_id=current_user.id).first_or_404()
    data = request.get_json() or {}
    if 'form_fields' in data:
        draft.form_fields = data['form_fields']
    draft.status = 'approved'
    db.session.commit()
    return jsonify(draft.to_dict())


@apply_api_bp.route('/submit/<uuid:application_id>', methods=['POST'])
@login_required
def mark_applied(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    app_record.stage = ApplicationStage.APPLIED.value
    app_record.applied_at = datetime.utcnow()
    if app_record.resume_version and app_record.resume_version.keyword_coverage:
        app_record.keyword_coverage_at_apply = app_record.resume_version.keyword_coverage
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id, status='approved'
    ).first()
    if draft:
        draft.status = 'submitted'
        draft.submitted_at = datetime.utcnow()
    activity_service.log(app_record.id, current_user.id, 'submit', subject='Marked applied manually')
    db.session.commit()
    return jsonify(app_record.to_dict())


@apply_api_bp.route('/batches', methods=['POST'])
@login_required
def create_batch():
    data = request.get_json() or {}
    app_ids = data.get('application_ids') or []
    if not app_ids:
        return jsonify({'error': 'application_ids required'}), 400
    try:
        batch = apply_batch_service.create_batch(current_user.id, app_ids)
        return jsonify(batch.to_dict()), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@apply_api_bp.route('/batches/<uuid:batch_id>/approve', methods=['POST'])
@login_required
def approve_batch(batch_id):
    from app.tasks.job_tasks import submit_apply_batch
    try:
        batch = apply_batch_service.approve_batch(current_user.id, batch_id)
        submit_apply_batch.delay(str(batch.id), str(current_user.id))
        return jsonify(batch.to_dict())
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@apply_api_bp.route('/batches/<uuid:batch_id>/status', methods=['GET'])
@login_required
def batch_status(batch_id):
    batch = ApplyBatch.query.filter_by(id=batch_id, user_id=current_user.id).first_or_404()
    items = ApplyBatchItem.query.filter_by(batch_id=batch.id).all()
    return jsonify({
        **batch.to_dict(),
        'items': [
            {
                'application_id': str(i.application_id),
                'status': i.status,
                'error_message': i.error_message,
                'proof_path': i.proof_path,
            }
            for i in items
        ],
    })
