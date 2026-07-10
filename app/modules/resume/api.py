"""Resume API routes."""

import io
import logging

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions.core import db
from app.models.jobs import MasterProfile, ResumeVersion, ResumeVersionStatus
from app.services.resume_export_service import resume_export_service
from app.services.resume_parser_service import resume_parser_service

logger = logging.getLogger(__name__)

resume_api_bp = Blueprint('resume_api', __name__, url_prefix='/api/v1/resume')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_api_bp.route('/profiles', methods=['GET'])
@login_required
def list_profiles():
    profiles = MasterProfile.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    return jsonify({'data': [p.to_dict() for p in profiles]})


@resume_api_bp.route('/profiles/<uuid:profile_id>', methods=['GET'])
@login_required
def get_profile(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = profile.to_dict()
    data['profile_data'] = profile.profile_data
    return jsonify(data)


@resume_api_bp.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename or not _allowed_file(file.filename):
        return jsonify({'error': 'Invalid file. Use PDF, DOCX, or TXT.'}), 400

    try:
        file_bytes = file.read()
        profile_data, confidence, extract_warnings = resume_parser_service.parse_file(
            file_bytes, file.filename
        )
        errors = resume_parser_service.validate_profile(profile_data)
        return jsonify({
            'profile_data': profile_data,
            'parse_confidence': confidence,
            'validation_errors': errors,
            'parse_diagnostics': resume_parser_service.get_parse_diagnostics(
                profile_data, extract_warnings
            ),
            'source_filename': secure_filename(file.filename),
        })
    except Exception as exc:
        logger.exception('Resume upload failed')
        return jsonify({'error': str(exc)}), 400


@resume_api_bp.route('/profiles', methods=['POST'])
@login_required
def save_profile():
    data = request.get_json() or {}
    profile_data = data.get('profile_data', {})
    errors = resume_parser_service.validate_profile(profile_data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400

    MasterProfile.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})

    profile = MasterProfile(
        user_id=current_user.id,
        headline=profile_data.get('headline', ''),
        profile_data=profile_data,
        source_filename=data.get('source_filename'),
        source_type=data.get('source_type'),
        parse_confidence=data.get('parse_confidence'),
        is_active=True,
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@resume_api_bp.route('/profiles/<uuid:profile_id>', methods=['PATCH'])
@login_required
def update_profile(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = request.get_json() or {}
    if 'profile_data' in data:
        errors = resume_parser_service.validate_profile(data['profile_data'])
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        profile.profile_data = data['profile_data']
    if 'headline' in data:
        profile.headline = data['headline']
    if 'is_active' in data and data['is_active']:
        MasterProfile.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
        profile.is_active = True
    elif 'is_active' in data:
        profile.is_active = False
    db.session.commit()
    return jsonify(profile.to_dict())


@resume_api_bp.route('/profiles/<uuid:profile_id>', methods=['DELETE'])
@login_required
def delete_profile(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    was_active = profile.is_active
    profile.soft_delete()
    if was_active:
        replacement = MasterProfile.query.filter_by(
            user_id=current_user.id, is_deleted=False
        ).order_by(MasterProfile.created_at.desc()).first()
        if replacement:
            replacement.is_active = True
    db.session.commit()
    return jsonify({'success': True})


@resume_api_bp.route('/profiles/<uuid:profile_id>/activate', methods=['POST'])
@login_required
def activate_profile(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    MasterProfile.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    profile.is_active = True
    db.session.commit()
    return jsonify(profile.to_dict())


@resume_api_bp.route('/profiles/<uuid:profile_id>/export', methods=['GET'])
@login_required
def export_profile(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    company = request.args.get('company', '')
    data = dict(profile.profile_data or {})
    if company:
        data['_target_company'] = company

    docx_bytes, filename = resume_export_service.export_docx(data)
    return send_file(
        io.BytesIO(docx_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@resume_api_bp.route('/profiles/<uuid:profile_id>/ats-test', methods=['POST'])
@login_required
def ats_test(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    docx_bytes, _ = resume_export_service.export_docx(profile.profile_data or {})
    result = resume_export_service.run_ats_parse_test(docx_bytes)
    return jsonify(result)
