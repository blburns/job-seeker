"""Applications web routes."""

import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import (
    Application, ApplicationStage, JobPosting, KeywordAnalysis, MasterProfile, ResumeVersion,
)
from app.services.apply_draft_service import apply_draft_service
from app.services.activity_service import activity_service
from app.services.pipeline_service import pipeline_service
from app.services.keyword_service import keyword_service
from app.services.tailoring_service import tailoring_service
from app.services.tailoring_diff_service import tailoring_diff_service
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

    applied_posting_ids = {
        row[0]
        for row in Application.query.filter_by(
            user_id=current_user.id, is_deleted=False
        ).with_entities(Application.job_posting_id).all()
    }
    available_postings = [p for p in postings if p.id not in applied_posting_ids]

    preselected_job_id = request.args.get('job_id')
    if request.method == 'GET' and preselected_job_id:
        existing = Application.query.filter_by(
            user_id=current_user.id,
            job_posting_id=preselected_job_id,
            is_deleted=False,
        ).first()
        if existing:
            flash('This job already has an application in your pipeline.', 'info')
            return redirect(url_for('applications.detail', application_id=existing.id))

    if request.method == 'POST':
        job_id = request.form.get('job_posting_id')
        if not job_id:
            flash('Please select a job posting.', 'warning')
            return render_template(
                'modules/applications/new.html',
                postings=available_postings,
                preselected_job_id=preselected_job_id,
            )

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

    return render_template(
        'modules/applications/new.html',
        postings=available_postings,
        preselected_job_id=preselected_job_id,
    )


@applications_bp.route('/queue')
@login_required
def apply_queue():
    apps = Application.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).filter(
        Application.stage.in_([
            ApplicationStage.SAVED.value,
            ApplicationStage.TAILORING.value,
            ApplicationStage.READY_TO_APPLY.value,
        ])
    ).order_by(Application.updated_at.desc()).all()
    return render_template('modules/applications/apply_queue.html', applications=apps)


@applications_bp.route('/batches')
@login_required
def batches_list():
    from app.models.jobs import ApplyBatch
    batches = ApplyBatch.query.filter_by(user_id=current_user.id).order_by(
        ApplyBatch.created_at.desc()
    ).all()
    return render_template('modules/applications/batches_list.html', batches=batches)


@applications_bp.route('/batches/create', methods=['POST'])
@login_required
def create_batch():
    from app.services.apply_batch_service import apply_batch_service
    app_ids = request.form.getlist('application_ids')
    if not app_ids:
        flash('Select at least one application.', 'warning')
        return redirect(url_for('applications.apply_queue'))
    try:
        batch = apply_batch_service.create_batch(current_user.id, app_ids)
        flash(f'Batch created with {len(app_ids)} applications.', 'success')
        return redirect(url_for('applications.batch_detail', batch_id=batch.id))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('applications.apply_queue'))


@applications_bp.route('/batches/<uuid:batch_id>')
@login_required
def batch_detail(batch_id):
    from app.models.jobs import ApplyBatch, ApplyBatchItem
    from app.services.apply_batch_service import apply_batch_service
    batch = ApplyBatch.query.filter_by(id=batch_id, user_id=current_user.id).first_or_404()
    items = ApplyBatchItem.query.filter_by(batch_id=batch.id).all()
    readiness = []
    for app_id in batch.application_ids or []:
        app = Application.query.filter_by(id=app_id, user_id=current_user.id).first()
        if app:
            readiness.append(apply_batch_service.application_readiness(current_user.id, app))
    return render_template(
        'modules/applications/batch_detail.html',
        batch=batch,
        items=items,
        readiness=readiness,
    )


@applications_bp.route('/batches/<uuid:batch_id>/approve', methods=['POST'])
@login_required
def approve_batch(batch_id):
    from app.services.apply_batch_service import apply_batch_service
    from app.tasks.job_tasks import submit_apply_batch
    try:
        apply_batch_service.approve_batch(current_user.id, batch_id)
        submit_apply_batch.delay(str(batch_id), str(current_user.id))
        flash('Batch approved. Applications are being submitted.', 'success')
    except ValueError as exc:
        flash(str(exc), 'danger')
    return redirect(url_for('applications.batch_detail', batch_id=batch_id))


@applications_bp.route('/batch-tailor', methods=['POST'])
@login_required
def batch_tailor():
    from app.tasks.job_tasks import batch_tailor_applications
    app_ids = request.form.getlist('application_ids')
    if app_ids:
        batch_tailor_applications.delay(app_ids, str(current_user.id))
        flash(f'Tailoring {len(app_ids)} applications in background.', 'success')
    return redirect(url_for('applications.apply_queue'))


@applications_bp.route('/<uuid:application_id>')
@login_required
def detail(application_id):
    from app.models.jobs import ApplicationActivity
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    version = app_record.resume_version
    activities = ApplicationActivity.query.filter_by(
        application_id=app_record.id
    ).order_by(ApplicationActivity.created_at.desc()).limit(50).all()
    return render_template(
        'modules/applications/detail.html',
        application=app_record,
        version=version,
        job=app_record.job_posting,
        activities=activities,
        diff_summary=tailoring_diff_service.summarize(version.diff_log if version else []),
        coverage_delta=tailoring_diff_service.coverage_delta(version.diff_log if version else []),
    )


@applications_bp.route('/<uuid:application_id>/notes', methods=['POST'])
@login_required
def save_notes(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    notes = request.form.get('notes', '').strip()
    previous = (app_record.notes or '').strip()
    app_record.notes = notes or None
    if notes != previous:
        activity_service.log(
            app_record.id,
            current_user.id,
            'note',
            subject='Notes updated' if notes else 'Notes cleared',
        )
    db.session.commit()
    flash('Notes saved.', 'success')
    return redirect(url_for('applications.detail', application_id=application_id))


@applications_bp.route('/<uuid:application_id>/tailoring')
@login_required
def tailoring_review(application_id):
    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    job = app_record.job_posting
    version_id = request.args.get('version_id')
    version_history = ResumeVersion.query.filter_by(
        user_id=current_user.id,
        job_posting_id=job.id,
        is_deleted=False,
    ).order_by(ResumeVersion.version_number.desc()).all()

    if version_id:
        version = ResumeVersion.query.filter_by(
            id=version_id, user_id=current_user.id, job_posting_id=job.id, is_deleted=False
        ).first_or_404()
    else:
        version = app_record.resume_version

    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    compare = {}
    compare_has_changes = False
    if version and profile:
        compare = tailoring_diff_service.build_compare(
            profile.profile_data or {},
            version.tailored_data or {},
        )
        compare_has_changes = tailoring_diff_service.compare_has_changes(compare)

    diff_log = version.diff_log if version else []
    draft = None
    resume_preview = ''
    if version:
        draft = apply_draft_service.ensure_draft(
            app_record,
            current_user.id,
            profile_data=version.tailored_data or {},
        )
        resume_preview = resume_export_service.render_preview_text(version.tailored_data or {})
        db.session.commit()

    return render_template(
        'modules/applications/tailoring_review.html',
        application=app_record,
        job=job,
        version=version,
        version_history=version_history,
        draft=draft,
        resume_preview=resume_preview,
        diff_summary=tailoring_diff_service.summarize(diff_log),
        coverage_delta=tailoring_diff_service.coverage_delta(diff_log),
        keyword_impact=tailoring_diff_service.keyword_impact(diff_log),
        overview=tailoring_diff_service.build_overview(
            diff_log,
            compare=compare,
            keyword_impact=tailoring_diff_service.keyword_impact(diff_log),
            job_title=job.title if job else '',
        ),
        compare=compare,
        compare_has_changes=compare_has_changes,
    )


@applications_bp.route('/<uuid:application_id>/tailoring/export')
@login_required
def tailoring_export(application_id):
    from flask import Response

    app_record = Application.query.filter_by(
        id=application_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    job = app_record.job_posting
    version_id = request.args.get('version_id')
    if version_id:
        version = ResumeVersion.query.filter_by(
            id=version_id, user_id=current_user.id, job_posting_id=job.id, is_deleted=False
        ).first_or_404()
    else:
        version = app_record.resume_version
    if not version:
        flash('No tailored resume to export.', 'warning')
        return redirect(url_for('applications.tailoring_review', application_id=application_id))

    report = tailoring_diff_service.export_text(
        version.diff_log,
        job_title=job.title if job else '',
        company=job.company if job else '',
    )
    filename = f"tailoring-report-v{version.version_number}.txt"
    return Response(
        report,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
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
    jd_text = f"{job.description or ''} {job.requirements or ''}"
    tailored, diff_log, coverage = tailoring_service.tailor_for_job_with_coverage(
        profile.profile_data or {},
        job.title,
        jd_text,
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
        keyword_coverage=coverage,
        export_filename=filename,
    )
    db.session.add(version)
    app_record.resume_version_id = version.id
    app_record.stage = ApplicationStage.TAILORING.value
    apply_draft_service.ensure_draft(
        app_record,
        current_user.id,
        profile_data=tailored,
        regenerate_cover_letter=True,
    )
    analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})
    db.session.add(KeywordAnalysis(
        user_id=current_user.id,
        job_posting_id=job.id,
        master_profile_id=profile.id,
        jd_keywords=analysis['jd_keywords'],
        matched_keywords=analysis['matched_keywords'],
        missing_keywords=analysis['missing_keywords'],
        synonym_matches=analysis['synonym_matches'],
        coverage_score=analysis['coverage_score'],
    ))
    activity_service.log(
        app_record.id,
        current_user.id,
        'tailor',
        subject='Resume tailored',
        description=tailoring_diff_service.export_text(
            diff_log, job.title, job.company,
        )[:4000],
    )
    db.session.commit()
    flash(f'Resume tailored. ATS score: {ats_result["score"]}%', 'success')
    return redirect(url_for('applications.tailoring_review', application_id=application_id))


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
    apply_draft_service.ensure_draft(
        app_record,
        current_user.id,
        profile_data=version.tailored_data if version else None,
        regenerate_cover_letter=True,
    )
    activity_service.log(app_record.id, current_user.id, 'approve', subject='Resume approved')
    db.session.commit()
    flash('Resume approved. Pre-fill draft created — review before submitting.', 'success')
    return redirect(url_for('apply.review', application_id=application_id))
