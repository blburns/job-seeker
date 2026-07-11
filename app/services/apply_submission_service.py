"""Automated application submission orchestration."""

import logging
import os
from datetime import datetime

from app.extensions.core import db
from app.models.jobs import (
    Application,
    ApplicationStage,
    ApplyDraft,
    ApplyBatchStatus,
    KeywordAnalysis,
    MasterProfile,
    ResumeVersion,
    SubmissionStatus,
)
from app.services.activity_service import activity_service
from app.services.apply_adapters import submit_application
from app.services.apply_adapters.base import ApplyContext
from app.services.apply_batch_service import apply_batch_service
from app.services.credential_vault_service import credential_vault_service
from app.services.resume_export_service import resume_export_service

logger = logging.getLogger(__name__)


class ApplySubmissionService:
    @classmethod
    def automation_blocked(cls) -> str:
        """Return a reason string if automation must not run, else empty."""
        from app.services.automation_kill_switch import is_automation_disabled, kill_switch_source

        if is_automation_disabled():
            source = kill_switch_source()
            return (
                f'Automation kill switch is on ({source}). '
                'Turn it off in Admin → Settings (file flag) or clear AUTOMATION_DISABLED in the environment.'
            )
        if os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() != 'true':
            return 'Apply automation disabled. Set APPLY_AUTOMATION_ENABLED=true.'
        return ''

    @classmethod
    def _resume_file_path(cls, application: Application) -> str:
        version = application.resume_version
        if not version:
            return ''
        export_dir = os.path.join('instance', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        path = os.path.join(export_dir, f'{application.id}.docx')
        if not os.path.exists(path):
            docx_bytes, _ = resume_export_service.export_docx(version.tailored_data or {})
            with open(path, 'wb') as f:
                f.write(docx_bytes)
        return path

    @classmethod
    def submit_application_record(cls, application_id, user_id) -> dict:
        blocked = cls.automation_blocked()
        # Kill switch always blocks; APPLY_AUTOMATION_ENABLED is also checked in adapters.
        if blocked and 'kill switch' in blocked.lower():
            raise RuntimeError(blocked)

        app_record = Application.query.filter_by(
            id=application_id, user_id=user_id, is_deleted=False
        ).first_or_404()
        job = app_record.job_posting
        draft = ApplyDraft.query.filter_by(
            application_id=app_record.id, user_id=user_id
        ).order_by(ApplyDraft.created_at.desc()).first()

        portal = 'generic'
        url = (job.url or app_record.portal_url or '').lower()
        if 'linkedin' in url:
            portal = 'linkedin'
        elif 'greenhouse' in url:
            portal = 'greenhouse'
        elif 'lever' in url:
            portal = 'lever'
        elif 'indeed' in url:
            portal = 'indeed'

        credentials = credential_vault_service.retrieve(user_id, portal)
        context = ApplyContext(
            application_id=str(app_record.id),
            job_url=job.url or app_record.portal_url or '',
            job_title=job.title,
            company=job.company,
            resume_path=cls._resume_file_path(app_record),
            form_fields=draft.form_fields if draft else {},
            user_id=str(user_id),
            portal_credentials=credentials,
        )
        result = submit_application(context)

        app_record.submission_status = result.status
        app_record.submission_proof = result.proof_path or None
        app_record.submission_error = result.message if not result.success else None

        if result.status == 'submitted':
            app_record.stage = ApplicationStage.APPLIED.value
            app_record.applied_at = datetime.utcnow()
            if app_record.resume_version and app_record.resume_version.keyword_coverage:
                app_record.keyword_coverage_at_apply = app_record.resume_version.keyword_coverage
            if draft:
                draft.status = 'submitted'
                draft.submitted_at = datetime.utcnow()
        elif result.status == 'needs_manual':
            app_record.stage = ApplicationStage.READY_TO_APPLY.value
            app_record.submission_status = SubmissionStatus.NEEDS_MANUAL.value

        activity_service.log(
            app_record.id,
            user_id,
            'auto_submit' if result.status == 'submitted' else 'submit',
            subject=f'Automated submission: {result.status}',
            description=result.message,
            metadata={
                'proof_path': result.proof_path,
                'portal': portal,
                'automated': True,
                'success': result.success,
            },
        )
        db.session.commit()
        return {
            'success': result.success,
            'status': result.status,
            'message': result.message,
            'proof_path': result.proof_path,
        }

    @classmethod
    def process_batch(cls, batch_id, user_id, application_ids=None):
        from app.models.jobs import ApplyBatch

        if cls.automation_blocked():
            raise RuntimeError(cls.automation_blocked())

        batch = ApplyBatch.query.filter_by(id=batch_id, user_id=user_id).first_or_404()
        batch.status = ApplyBatchStatus.RUNNING.value
        db.session.commit()

        targets = application_ids or batch.application_ids or []
        for app_id in targets:
            try:
                result = cls.submit_application_record(app_id, user_id)
                apply_batch_service.mark_item_result(
                    batch_id,
                    app_id,
                    result['status'],
                    result.get('proof_path', ''),
                    '' if result['success'] else result.get('message', ''),
                )
            except Exception as exc:
                logger.exception('Batch submit failed for %s', app_id)
                apply_batch_service.mark_item_result(batch_id, app_id, 'failed', '', str(exc))

        apply_batch_service.finalize_batch(batch_id)
        return batch


apply_submission_service = ApplySubmissionService()
