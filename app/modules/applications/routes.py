"""Applications web routes."""

import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import (
    Application, ApplicationStage, JobPosting, MasterProfile, ResumeVersion,
)
from app.services.pipeline_service import pipeline_service
from app.services.tailoring_service import tailoring_service
from app.services.resume_export_service import resume_export_service
from . import applications_bp

logger = logging.getLogger(__name__)


@applications_bp.route('/')
@login_required
def index():
    return redirect(url_for('applications.dashboard'))


@applications_bp.route('/dashboard')
@login_required
def dashboard():
    apps = Application.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    pipeline = pipeline_service.get_pipeline_data(current_user.id, apps)
    return render_template('modules/applications/dashboard.html', pipeline=pipeline, applications=apps)


@applications_bp.route('/list')
@login_required
def list_view():
    apps = Application.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(Application.created_at.desc()).all()
    return render_template('modules/applications/list.html', applications=apps)


@applications_bp.route('/pipeline')
@login_required
def pipeline():
    pipeline_data = pipeline_service.get_pipeline_data(current_user.id)
    return render_template(
        'modules/applications/pipeline.html',
        pipeline=pipeline_data,
        stages=pipeline_service.STAGES,
    )


@applications_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_application():
    postings = JobPosting.query.filter_by(
        user_id=current_user.id, is_deleted=False, is_active=True
    ).order_by(JobPosting.created_at.desc()).all()

    if request.method == 'POST':
        job_id = request.form.get('job_posting_id')
        if not job_id:
            flash('Please select a job posting.', 'warning')
            return render_template('modules/applications/new.html', postings=postings)

        job = JobPosting.query.filter_by(id=job_id, user_id=current_user.id).first_or_404()
        existing = Application.query.filter_by(
            user_id=current_user.id, job_posting_id=job.id, is_deleted=False
        ).first()
        if existing:
            flash('Application already exists for this job.', 'info')
            return redirect(url_for('applications.detail', application_id=existing.id))

        app_record = Application(
            user_id=current_user.id,
            job_posting_id=job.id,
            stage=ApplicationStage.SAVED.value,
            portal_url=job.url,
        )
        db.session.add(app_record)
        db.session.commit()
        flash('Application created.', 'success')
        return redirect(url_for('applications.detail', application_id=app_record.id))

    return render_template('modules/applications/new.html', postings=postings)


@applications_bp.route('/<uuid:application_id>')
@login_required
def detail(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    version = app_record.resume_version
    return render_template(
        'modules/applications/detail.html',
        application=app_record,
        version=version,
        job=app_record.job_posting,
    )


@applications_bp.route('/<uuid:application_id>/tailor', methods=['POST'])
@login_required
def tailor(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    if not profile:
        flash('Upload a master profile first.', 'warning')
        return redirect(url_for('applications.detail', application_id=application_id))

    job = app_record.job_posting
    tailored, diff_log = tailoring_service.tailor_for_job(
        profile.profile_data or {},
        job.title,
        f"{job.description or ''} {job.requirements or ''}",
        job.company,
    )
    docx_bytes, filename = resume_export_service.export_docx(tailored)
    ats_result = resume_export_service.run_ats_parse_test(docx_bytes)

    from app.models.jobs import ResumeVersionStatus
    version_count = ResumeVersion.query.filter_by(user_id=current_user.id, job_posting_id=job.id).count()
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
    app_record.resume_version_id = version.id
    app_record.stage = ApplicationStage.TAILORING.value
    db.session.commit()
    flash(f'Resume tailored. ATS score: {ats_result["score"]}%', 'success')
    return redirect(url_for('applications.detail', application_id=application_id))


@applications_bp.route('/<uuid:application_id>/approve', methods=['POST'])
@login_required
def approve(application_id):
    from datetime import datetime
    from app.models.jobs import ResumeVersionStatus

    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    if not app_record.resume_version_id:
        flash('No tailored resume to approve.', 'warning')
        return redirect(url_for('applications.detail', application_id=application_id))

    version = ResumeVersion.query.get(app_record.resume_version_id)
    version.status = ResumeVersionStatus.APPROVED.value
    version.approved_at = datetime.utcnow()
    version.approved_by = current_user.id
    app_record.stage = ApplicationStage.READY_TO_APPLY.value
    db.session.commit()
    flash('Resume approved. Ready to apply.', 'success')
    return redirect(url_for('applications.detail', application_id=application_id))
