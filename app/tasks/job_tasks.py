"""Celery tasks for job seeker automation."""

import logging
from datetime import datetime, timedelta

from celery import shared_task

from app.extensions.core import db

logger = logging.getLogger(__name__)


@shared_task(name='app.tasks.job_tasks.run_discovery_for_profile')
def run_discovery_for_profile(profile_id, user_id):
    from app.services.discovery_orchestrator import discovery_orchestrator
    try:
        discovery_orchestrator.run_discovery(profile_id, user_id)
        return {'success': True, 'profile_id': str(profile_id)}
    except Exception as exc:
        logger.exception('Discovery task failed')
        return {'success': False, 'error': str(exc)}


@shared_task(name='app.tasks.job_tasks.run_all_active_discoveries')
def run_all_active_discoveries():
    from app.models.jobs import JobSearchProfile
    from app.services.discovery_orchestrator import discovery_orchestrator

    profiles = JobSearchProfile.query.filter_by(is_active=True, is_deleted=False).all()
    count = 0
    for profile in profiles:
        hours = profile.schedule_hours or 6
        if profile.last_run_at and profile.last_run_at > datetime.utcnow() - timedelta(hours=hours):
            continue
        discovery_orchestrator.run_discovery(profile.id, profile.user_id)
        count += 1
    return {'success': True, 'profiles_run': count}


@shared_task(name='app.tasks.job_tasks.batch_tailor_applications')
def batch_tailor_applications(application_ids, user_id):
    from app.models.jobs import Application, ApplicationStage, KeywordAnalysis, MasterProfile, ResumeVersion, ResumeVersionStatus
    from app.services.activity_service import activity_service
    from app.services.keyword_service import keyword_service
    from app.services.resume_export_service import resume_export_service
    from app.services.tailoring_service import tailoring_service

    profile = MasterProfile.query.filter_by(user_id=user_id, is_active=True, is_deleted=False).first()
    if not profile:
        return {'success': False, 'error': 'No active profile'}

    tailored_count = 0
    for app_id in application_ids:
        app_record = Application.query.filter_by(id=app_id, user_id=user_id, is_deleted=False).first()
        if not app_record:
            continue
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
        version_count = ResumeVersion.query.filter_by(user_id=user_id, job_posting_id=job.id).count()
        version = ResumeVersion(
            user_id=user_id,
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

        analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})
        db.session.add(KeywordAnalysis(
            user_id=user_id,
            job_posting_id=job.id,
            master_profile_id=profile.id,
            jd_keywords=analysis['jd_keywords'],
            matched_keywords=analysis['matched_keywords'],
            missing_keywords=analysis['missing_keywords'],
            synonym_matches=analysis['synonym_matches'],
            coverage_score=analysis['coverage_score'],
        ))
        activity_service.log(app_record.id, user_id, 'tailor', subject='Batch tailored')
        tailored_count += 1

    db.session.commit()
    return {'success': True, 'tailored': tailored_count}


@shared_task(name='app.tasks.job_tasks.submit_apply_batch')
def submit_apply_batch(batch_id, user_id):
    from app.services.apply_submission_service import apply_submission_service
    try:
        batch = apply_submission_service.process_batch(batch_id, user_id)
        return {'success': True, 'batch_id': str(batch.id), 'status': batch.status}
    except Exception as exc:
        logger.exception('Apply batch failed')
        return {'success': False, 'error': str(exc)}


@shared_task(name='app.tasks.job_tasks.check_follow_up_reminders')
def check_follow_up_reminders():
    from datetime import datetime, timedelta
    from app.models.jobs import Application, ApplicationStage
    from app.services.activity_service import activity_service

    cutoff = datetime.utcnow() - timedelta(days=7)
    apps = Application.query.filter(
        Application.stage == ApplicationStage.APPLIED.value,
        Application.applied_at <= cutoff,
        Application.response_at.is_(None),
        Application.is_deleted == False,  # noqa: E712
    ).all()
    reminded = 0
    for app in apps:
        if app.follow_up_at and app.follow_up_at > datetime.utcnow():
            continue
        activity_service.log(
            app.id,
            app.user_id,
            'follow_up_due',
            subject='Follow-up reminder',
            description=f'No response since {app.applied_at}',
        )
        app.follow_up_at = datetime.utcnow() + timedelta(days=3)
        reminded += 1
        try:
            from app.models.auth import User
            from app.tasks.email_tasks import send_email_async
            user = User.query.get(app.user_id)
            if user and user.email:
                send_email_async.delay(
                    user.email,
                    'Follow-up reminder',
                    f'No response yet for your application. Consider following up.',
                )
        except Exception:
            logger.debug('Follow-up email skipped')
    db.session.commit()
    return {'success': True, 'reminded': reminded}


@shared_task(name='app.tasks.job_tasks.check_portal_sessions')
def check_portal_sessions():
    from app.models.jobs import PortalCredential
    from app.services.scraping.session_health import session_health

    creds = PortalCredential.query.filter_by(is_active=True, is_deleted=False).filter(
        PortalCredential.portal.in_(['linkedin', 'indeed'])
    ).all()
    checked = 0
    failed = 0
    for cred in creds:
        result = session_health.check_and_update_credential(cred.user_id, cred.portal)
        checked += 1
        if not result.ok:
            failed += 1
    return {'success': True, 'checked': checked, 'failed': failed}
