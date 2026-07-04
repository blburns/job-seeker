"""Resume web routes."""

import json
import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import MasterProfile
from app.services.resume_export_service import resume_export_service
from app.services.resume_parser_service import resume_parser_service
from app.services.profile_form_service import profile_form_service
from . import resume_bp

logger = logging.getLogger(__name__)


def _save_master_profile(user_id, profile_data, source_filename='manual_entry', parse_confidence='100', set_active=True):
    if set_active:
        MasterProfile.query.filter_by(user_id=user_id, is_active=True).update({'is_active': False})
    profile = MasterProfile(
        user_id=user_id,
        headline=profile_data.get('headline', ''),
        profile_data=profile_data,
        source_filename=source_filename,
        source_type='manual',
        parse_confidence=parse_confidence,
        is_active=set_active,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def _render_manual_form(profile=None, form=None, validation_errors=None):
    if form is None:
        form = (
            profile_form_service.profile_to_form_context(profile.profile_data or {})
            if profile else profile_form_service.empty_form_context()
        )
    return render_template(
        'modules/resume/manual_profile_form.html',
        profile=profile,
        form=form,
        validation_errors=validation_errors or [],
    )


@resume_bp.route('/')
@login_required
def index():
    return redirect(url_for('resume.profiles_list'))


@resume_bp.route('/profiles')
@login_required
def profiles_list():
    profiles = MasterProfile.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(MasterProfile.created_at.desc()).all()
    active = next((p for p in profiles if p.is_active), None)
    return render_template(
        'modules/resume/profiles_list.html',
        profiles=profiles,
        active_profile=active,
    )


@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Please select a file.', 'warning')
            return render_template('modules/resume/upload.html')

        file = request.files['file']
        if not file.filename:
            flash('Please select a file.', 'warning')
            return render_template('modules/resume/upload.html')

        try:
            file_bytes = file.read()
            profile_data, confidence = resume_parser_service.parse_file(file_bytes, file.filename)
            errors = resume_parser_service.validate_profile(profile_data)
            diagnostics = resume_parser_service.get_parse_diagnostics(profile_data)
            return render_template(
                'modules/resume/review.html',
                profile_data=profile_data,
                profile_json=json.dumps(profile_data, indent=2),
                parse_confidence=confidence,
                validation_errors=errors,
                parse_diagnostics=diagnostics,
                source_filename=file.filename,
            )
        except Exception as exc:
            logger.exception('Resume parse failed')
            flash(f'Failed to parse resume: {exc}', 'danger')
            return render_template('modules/resume/upload.html')

    return render_template('modules/resume/upload.html')


@resume_bp.route('/profiles/manual', methods=['GET', 'POST'])
@login_required
def profile_manual():
    if request.method == 'POST':
        profile_data = profile_form_service.build_profile_from_form(request.form)
        errors = resume_parser_service.validate_profile(profile_data)
        if errors:
            for err in errors:
                flash(err, 'warning')
            form = profile_form_service.profile_to_form_context(profile_data)
            return _render_manual_form(form=form, validation_errors=errors)

        profile = _save_master_profile(current_user.id, profile_data)
        flash('Master profile created successfully.', 'success')
        return redirect(url_for('resume.profile_detail', profile_id=profile.id))

    return _render_manual_form()


@resume_bp.route('/profiles/<uuid:profile_id>/manual', methods=['GET', 'POST'])
@login_required
def profile_manual_edit(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()

    if request.method == 'POST':
        profile_data = profile_form_service.build_profile_from_form(
            request.form, existing=profile.profile_data
        )
        errors = resume_parser_service.validate_profile(profile_data)
        if errors:
            for err in errors:
                flash(err, 'warning')
            form = profile_form_service.profile_to_form_context(profile_data)
            return _render_manual_form(profile=profile, form=form, validation_errors=errors)

        profile.profile_data = profile_data
        profile.headline = profile_data.get('headline', '')
        db.session.commit()
        flash('Master profile updated.', 'success')
        return redirect(url_for('resume.profile_detail', profile_id=profile.id))

    return _render_manual_form(profile=profile)


@resume_bp.route('/review', methods=['POST'])
@login_required
def save_reviewed():
    profile_data = json.loads(request.form.get('profile_data', '{}'))
    errors = resume_parser_service.validate_profile(profile_data)
    if errors:
        for err in errors:
            flash(err, 'warning')
        return render_template(
            'modules/resume/review.html',
            profile_data=profile_data,
            profile_json=json.dumps(profile_data, indent=2),
            parse_confidence=request.form.get('parse_confidence'),
            validation_errors=errors,
            source_filename=request.form.get('source_filename'),
        )

    MasterProfile.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    profile = MasterProfile(
        user_id=current_user.id,
        headline=profile_data.get('headline', ''),
        profile_data=profile_data,
        source_filename=request.form.get('source_filename'),
        parse_confidence=request.form.get('parse_confidence'),
        is_active=True,
    )
    db.session.add(profile)
    db.session.commit()
    flash('Master profile saved successfully.', 'success')
    return redirect(url_for('resume.profile_detail', profile_id=profile.id))


@resume_bp.route('/profiles/<uuid:profile_id>')
@login_required
def profile_detail(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    ats_result = None
    if profile.profile_data:
        docx_bytes, _ = resume_export_service.export_docx(profile.profile_data)
        ats_result = resume_export_service.run_ats_parse_test(docx_bytes)
    return render_template(
        'modules/resume/profile_detail.html',
        profile=profile,
        profile_json=json.dumps(profile.profile_data or {}, indent=2),
        ats_result=ats_result,
    )


@resume_bp.route('/profiles/<uuid:profile_id>/delete', methods=['POST'])
@login_required
def profile_delete(profile_id):
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
    flash('Master profile deleted.', 'success')
    return redirect(url_for('resume.profiles_list'))


@resume_bp.route('/profiles/<uuid:profile_id>/activate', methods=['POST'])
@login_required
def profile_activate(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    MasterProfile.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    profile.is_active = True
    db.session.commit()
    flash(f'"{profile.full_name}" is now your active profile.', 'success')
    return redirect(url_for('resume.profiles_list'))


@resume_bp.route('/profiles/<uuid:profile_id>/edit', methods=['GET', 'POST'])
@login_required
def profile_edit(profile_id):
    profile = MasterProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()

    if request.method == 'POST':
        profile_data = json.loads(request.form.get('profile_data', '{}'))
        errors = resume_parser_service.validate_profile(profile_data)
        if errors:
            for err in errors:
                flash(err, 'warning')
        else:
            profile.profile_data = profile_data
            profile.headline = profile_data.get('headline', '')
            db.session.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('resume.profile_detail', profile_id=profile.id))

    return render_template(
        'modules/resume/profile_edit.html',
        profile=profile,
        profile_json=json.dumps(profile.profile_data or {}, indent=2),
    )
