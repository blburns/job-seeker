"""Apply batch orchestration and business rules."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List

from app.extensions.core import db
from app.models.jobs import (
    Application,
    ApplicationStage,
    ApplyBatch,
    ApplyBatchItem,
    ApplyBatchStatus,
    ApplyDraft,
    MasterProfile,
    ResumeVersion,
    ResumeVersionStatus,
    SubmissionStatus,
)

from app.services.apply_draft_service import apply_draft_service


class ApplyBatchService:
    DAILY_CAP = int(os.getenv('DAILY_APPLY_CAP', '25'))

    @classmethod
    def create_batch(cls, user_id, application_ids: List[str]) -> ApplyBatch:
        unique_ids = list(dict.fromkeys(str(aid) for aid in application_ids))
        apps = Application.query.filter(
            Application.id.in_(unique_ids),
            Application.user_id == user_id,
            Application.is_deleted == False,  # noqa: E712
        ).all()
        if not apps:
            raise ValueError('No valid applications selected')

        batch = ApplyBatch(
            user_id=user_id,
            status=ApplyBatchStatus.DRAFT.value,
            application_ids=[str(a.id) for a in apps],
        )
        db.session.add(batch)
        db.session.flush()
        for app in apps:
            db.session.add(ApplyBatchItem(
                batch_id=batch.id,
                application_id=app.id,
                status='pending',
            ))
        db.session.commit()
        return batch

    @classmethod
    def application_readiness(cls, user_id, app: Application) -> Dict[str, Any]:
        job = app.job_posting
        job_label = f'{job.title} @ {job.company}' if job else str(app.id)
        version = app.resume_version
        resume_tailored = version is not None
        resume_approved = bool(
            version and version.status == ResumeVersionStatus.APPROVED.value
        )
        draft = ApplyDraft.query.filter_by(
            application_id=app.id, user_id=user_id
        ).order_by(ApplyDraft.created_at.desc()).first()
        draft_complete = apply_draft_service.is_complete(draft)
        issues = []
        if not resume_tailored:
            issues.append('Tailor resume')
        elif not resume_approved:
            issues.append('Approve tailored resume')
        if not draft_complete:
            issues.append('Complete apply pre-fill (email required)')
        return {
            'application_id': str(app.id),
            'job_label': job_label,
            'resume_tailored': resume_tailored,
            'resume_approved': resume_approved,
            'draft_complete': draft_complete,
            'ready': resume_approved and draft_complete,
            'issues': issues,
        }

    @classmethod
    def prepare_batch(cls, user_id, batch: ApplyBatch) -> None:
        """Auto-create apply drafts where possible before validation."""
        for app_id in batch.application_ids or []:
            app = Application.query.filter_by(id=app_id, user_id=user_id).first()
            if not app:
                continue
            apply_draft_service.ensure_draft(app, user_id)
        db.session.commit()

    @classmethod
    def validate_for_approve(cls, user_id, batch: ApplyBatch) -> List[str]:
        cls.prepare_batch(user_id, batch)
        errors = []
        profile = MasterProfile.query.filter_by(
            user_id=user_id, is_active=True, is_deleted=False
        ).first()
        if not profile:
            errors.append('No active master profile')

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        applied_today = Application.query.filter(
            Application.user_id == user_id,
            Application.applied_at >= today_start,
            Application.is_deleted == False,  # noqa: E712
        ).count()
        pending = len(batch.application_ids or [])
        if applied_today + pending > cls.DAILY_CAP:
            errors.append(f'Daily apply cap ({cls.DAILY_CAP}) would be exceeded')

        for app_id in batch.application_ids or []:
            app = Application.query.filter_by(id=app_id, user_id=user_id).first()
            if not app:
                errors.append(f'Application {app_id} not found')
                continue
            dup = Application.query.filter(
                Application.user_id == user_id,
                Application.job_posting_id == app.job_posting_id,
                Application.id != app.id,
                Application.stage == ApplicationStage.APPLIED.value,
                Application.is_deleted == False,  # noqa: E712
            ).first()
            if dup:
                errors.append(f'Duplicate apply blocked for {app.job_posting_id}')
            version = app.resume_version
            job_label = app.job_posting.title if app.job_posting else str(app_id)
            if not version or version.status != ResumeVersionStatus.APPROVED.value:
                errors.append(
                    f'"{job_label}": approve the tailored resume '
                    f'(Applications → open job → Approve Resume)'
                )
            draft = ApplyDraft.query.filter_by(
                application_id=app.id, user_id=user_id
            ).order_by(ApplyDraft.created_at.desc()).first()
            if not apply_draft_service.is_complete(draft):
                errors.append(
                    f'"{job_label}": add email in Review & Apply pre-fill '
                    f'(or set email on your master profile)'
                )
        return errors

    @classmethod
    def approve_batch(cls, user_id, batch_id):
        batch = ApplyBatch.query.filter_by(id=batch_id, user_id=user_id).first_or_404()
        errors = cls.validate_for_approve(user_id, batch)
        if errors:
            raise ValueError('; '.join(errors))
        batch.status = ApplyBatchStatus.APPROVED.value
        batch.approved_at = datetime.utcnow()
        for app_id in batch.application_ids or []:
            app = Application.query.get(app_id)
            if app:
                app.apply_batch_id = batch.id
                app.submission_status = SubmissionStatus.PENDING.value
        db.session.commit()
        return batch

    @classmethod
    def mark_item_result(cls, batch_id, application_id, status: str, proof_path: str = '', error: str = ''):
        item = ApplyBatchItem.query.filter_by(
            batch_id=batch_id, application_id=application_id
        ).first()
        if item:
            item.status = status
            item.proof_path = proof_path or None
            item.error_message = error or None
            item.submission_status = status
        db.session.commit()

    @classmethod
    def finalize_batch(cls, batch_id):
        batch = ApplyBatch.query.get(batch_id)
        if not batch:
            return
        items = ApplyBatchItem.query.filter_by(batch_id=batch_id).all()
        failed = [i for i in items if i.status in ('failed', 'needs_manual')]
        batch.status = (
            ApplyBatchStatus.PARTIAL_FAILURE.value if failed else ApplyBatchStatus.COMPLETED.value
        )
        batch.completed_at = datetime.utcnow()
        db.session.commit()


apply_batch_service = ApplyBatchService()
