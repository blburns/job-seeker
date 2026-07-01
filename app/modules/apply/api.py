"""Apply API routes."""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import Application, ApplicationStage, ApplyDraft, MasterProfile
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
    draft = ApplyDraft(
        application_id=app_record.id,
        user_id=current_user.id,
        form_fields=form_fields,
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
    draft = ApplyDraft.query.filter_by(
        application_id=app_record.id, user_id=current_user.id, status='approved'
    ).first()
    if draft:
        draft.status = 'submitted'
        draft.submitted_at = datetime.utcnow()
    db.session.commit()
    return jsonify(app_record.to_dict())
