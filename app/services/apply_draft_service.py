"""Create and validate apply pre-fill drafts."""

import logging
from typing import Any, Dict, Optional

from app.extensions.core import db
from app.models.jobs import ApplyDraft, MasterProfile
from app.services.job_discovery_service import job_discovery_service
from app.services.tailoring_service import tailoring_service

logger = logging.getLogger(__name__)


class ApplyDraftService:
    @classmethod
    def ensure_draft(
        cls,
        application,
        user_id,
        *,
        profile_data: Optional[Dict[str, Any]] = None,
        regenerate_cover_letter: bool = False,
    ) -> Optional[ApplyDraft]:
        """Return an apply draft, creating or refreshing cover letter when needed."""
        draft = ApplyDraft.query.filter_by(
            application_id=application.id,
            user_id=user_id,
        ).order_by(ApplyDraft.created_at.desc()).first()

        profile = MasterProfile.query.filter_by(
            user_id=user_id, is_active=True, is_deleted=False
        ).first()
        if not profile:
            return draft

        job = application.job_posting
        if not job:
            return draft

        letter_profile = profile_data or profile.profile_data or {}
        contact = letter_profile.get('contact', {})

        if draft:
            cls._backfill_from_profile(draft, contact)
            if regenerate_cover_letter or not (draft.cover_letter or '').strip():
                draft.cover_letter = cls._generate_cover_letter(job, letter_profile)
            return draft

        form_fields = job_discovery_service.build_apply_draft(
            profile.profile_data or {},
            {'title': job.title, 'company': job.company, 'url': job.url},
        )
        cover_letter = cls._generate_cover_letter(job, letter_profile)

        draft = ApplyDraft(
            application_id=application.id,
            user_id=user_id,
            form_fields=form_fields,
            cover_letter=cover_letter,
            status='draft',
        )
        db.session.add(draft)
        db.session.flush()
        return draft

    @classmethod
    def _generate_cover_letter(cls, job, profile_data: Dict[str, Any]) -> str:
        try:
            return tailoring_service.generate_cover_letter_for_job(
                profile_data,
                job.title,
                job.company,
                f"{job.description or ''} {job.requirements or ''}",
            )
        except Exception as exc:
            logger.warning('Cover letter generation failed: %s', exc)
            contact = profile_data.get('contact', {})
            name = contact.get('name', 'Applicant')
            return (
                f'Dear Hiring Manager,\n\n'
                f'I am writing to express my interest in the {job.title} position at {job.company}.\n\n'
                f'Sincerely,\n{name}'
            )

    @classmethod
    def _backfill_from_profile(cls, draft: ApplyDraft, contact: Dict[str, Any]) -> None:
        fields = dict(draft.form_fields or {})
        changed = False
        for key, profile_key in (
            ('email', 'email'),
            ('full_name', 'name'),
            ('phone', 'phone'),
            ('location', 'location'),
        ):
            if not (fields.get(key) or '').strip() and (contact.get(profile_key) or '').strip():
                fields[key] = contact[profile_key]
                changed = True
        if changed:
            draft.form_fields = fields

    @classmethod
    def is_complete(cls, draft: Optional[ApplyDraft]) -> bool:
        return bool(draft and (draft.form_fields or {}).get('email', '').strip())


apply_draft_service = ApplyDraftService()
