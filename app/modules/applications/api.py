"""Applications API routes."""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import (
    Application, ApplicationActivity, ApplicationStage, JobPosting, MasterProfile,
    ResumeVersion, ResumeVersionStatus,
)
from app.services.pipeline_service import pipeline_service
from app.services.resume_export_service import resume_export_service
from app.services.tailoring_service import tailoring_service
from app.utils.security import sanitize_input

logger = logging.getLogger(__name__)

applications_api_bp = Blueprint('applications_api', __name__, url_prefix='/api/v1/applications')


@applications_api_bp.route('/', methods=['GET'])
@login_required
def list_applications():
    apps = Application.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(Application.created_at.desc()).all()
    return jsonify({'data': [a.to_dict() for a in apps]})


@applications_api_bp.route('/', methods=['POST'])
@login_required
def create_application():
    data = request.get_json() or {}
    job_posting_id = data.get('job_posting_id')
    if not job_posting_id:
        return jsonify({'error': 'job_posting_id is required'}), 400

    job = JobPosting.query.filter_by(
        id=job_posting_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()

    existing = Application.query.filter_by(
        user_id=current_user.id, job_posting_id=job.id, is_deleted=False
    ).first()
    if existing:
        return jsonify(existing.to_dict()), 200

    app_record = Application(
        user_id=current_user.id,
        job_posting_id=job.id,
        stage=ApplicationStage.SAVED.value,
        portal_url=job.url,
    )
    db.session.add(app_record)
    db.session.commit()
    return jsonify(app_record.to_dict()), 201


@applications_api_bp.route('/pipeline', methods=['GET'])
@login_required
def pipeline_api():
    data = pipeline_service.get_pipeline_data(current_user.id)
    return jsonify(data)


@applications_api_bp.route('/<uuid:application_id>/stage', methods=['PATCH'])
@login_required
def update_stage(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = request.get_json() or {}
    new_stage = data.get('stage')
    try:
        pipeline_service.update_stage(app_record, new_stage)
        db.session.commit()
        return jsonify(app_record.to_dict())
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400


@applications_api_bp.route('/<uuid:application_id>/tailor', methods=['POST'])
@login_required
def tailor_resume(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    if not profile:
        return jsonify({'error': 'No active master profile'}), 400

    job = app_record.job_posting
    tailored, diff_log = tailoring_service.tailor_for_job(
        profile.profile_data or {},
        job.title,
        f"{job.description or ''} {job.requirements or ''}",
        job.company,
    )
    errors = tailoring_service.validate_diff(diff_log, profile.profile_data or {})
    if errors:
        return jsonify({'error': 'Invalid tailoring', 'details': errors}), 400

    docx_bytes, filename = resume_export_service.export_docx(tailored)
    ats_result = resume_export_service.run_ats_parse_test(docx_bytes)

    version_count = ResumeVersion.query.filter_by(
        user_id=current_user.id, job_posting_id=job.id
    ).count()

    version = ResumeVersion(
        user_id=current_user.id,
        master_profile_id=profile.id,
        job_posting_id=job.id,
        version_number=version_count + 1,
        status=ResumeVersionStatus.PENDING_APPROVAL.value,
        tailored_data=tailored,
        diff_log=diff_log,
        ats_score=ats_result['score'],
        export_filename=filename,
    )
    db.session.add(version)
    db.session.flush()
    app_record.resume_version_id = version.id
    app_record.stage = ApplicationStage.TAILORING.value
    db.session.commit()
    return jsonify({
        'version': version.to_dict(),
        'ats_result': ats_result,
        'diff_log': diff_log,
    })


@applications_api_bp.route('/<uuid:application_id>/approve', methods=['POST'])
@login_required
def approve_resume(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    if not app_record.resume_version_id:
        return jsonify({'error': 'No resume version to approve'}), 400

    version = ResumeVersion.query.filter_by(
        id=app_record.resume_version_id, user_id=current_user.id
    ).first_or_404()
    version.status = ResumeVersionStatus.APPROVED.value
    version.approved_at = datetime.utcnow()
    version.approved_by = current_user.id
    app_record.stage = ApplicationStage.READY_TO_APPLY.value
    db.session.commit()
    return jsonify({'application': app_record.to_dict(), 'version': version.to_dict()})


@applications_api_bp.route('/<uuid:application_id>', methods=['GET'])
@login_required
def get_application(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    result = app_record.to_dict()
    if app_record.resume_version:
        result['resume_version'] = app_record.resume_version.to_dict()
        result['resume_version']['tailored_data'] = app_record.resume_version.tailored_data
    return jsonify(result)


@applications_api_bp.route('/<uuid:application_id>', methods=['DELETE'])
@login_required
def delete_application(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    app_record.soft_delete()
    db.session.commit()
    return jsonify({'success': True, 'id': str(app_record.id)})


@applications_api_bp.route('/<uuid:application_id>/notes', methods=['POST'])
@login_required
def save_notes_api(application_id):
    from app.services.activity_service import activity_service

    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = request.get_json() or {}
    notes = (data.get('notes') or '').strip()
    previous = (app_record.notes or '').strip()
    app_record.notes = notes or None
    if notes != previous:
        activity_service.log(
            app_record.id,
            current_user.id,
            'note',
            subject='Notes updated',
            description=notes[:200] if notes else 'Notes cleared',
        )
    db.session.commit()
    return jsonify(app_record.to_dict())
