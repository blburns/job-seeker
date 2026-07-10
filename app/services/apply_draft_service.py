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
                try:
                    draft.cover_letter = cls._generate_cover_letter(job, letter_profile)
                except Exception as exc:
                    logger.warning('Cover letter generation failed: %s', exc)
                    if not (draft.cover_letter or '').strip():
                        draft.cover_letter = cls._fallback_cover_letter(job, letter_profile)
            return draft

        form_fields = job_discovery_service.build_apply_draft(
            profile.profile_data or {},
            {'title': job.title, 'company': job.company, 'url': job.url},
        )
        try:
            cover_letter = cls._generate_cover_letter(job, letter_profile)
        except Exception as exc:
            logger.warning('Cover letter generation failed: %s', exc)
            cover_letter = cls._fallback_cover_letter(job, letter_profile)

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
    def _fallback_cover_letter(cls, job, profile_data: Dict[str, Any]) -> str:
        contact = profile_data.get('contact', {})
        name = contact.get('name', 'Applicant')
        return (
            f'Dear Hiring Manager,\n\n'
            f'I am writing to express my interest in the {job.title} position at {job.company}.\n\n'
            f'Sincerely,\n{name}'
        )

    @classmethod
    def _generate_cover_letter(cls, job, profile_data: Dict[str, Any]) -> str:
        return tailoring_service.generate_cover_letter_for_job(
            profile_data,
            job.title,
            job.company,
            f"{job.description or ''} {job.requirements or ''}",
        )

    @classmethod
    def regenerate_cover_letter(
        cls,
        application,
        user_id,
        *,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Regenerate cover letter and return status for UI messaging.

        Returns dict: {draft, ok, error, rate_limited}
        """
        draft = cls.ensure_draft(application, user_id, profile_data=profile_data)
        if not draft:
            return {
                'draft': None,
                'ok': False,
                'error': 'No draft available — upload a master profile first.',
                'rate_limited': False,
            }

        profile = MasterProfile.query.filter_by(
            user_id=user_id, is_active=True, is_deleted=False
        ).first()
        job = application.job_posting
        if not profile or not job:
            return {
                'draft': draft,
                'ok': False,
                'error': 'Missing profile or job posting.',
                'rate_limited': False,
            }

        letter_profile = profile_data or profile.profile_data or {}
        previous = draft.cover_letter or ''
        try:
            new_letter = (cls._generate_cover_letter(job, letter_profile) or '').strip()
        except Exception as exc:
            logger.warning('Cover letter regeneration failed: %s', exc)
            message = str(exc)
            rate_limited = (
                '429' in message
                or 'rate limit' in message.lower()
                or 'quota' in message.lower()
            )
            return {
                'draft': draft,
                'ok': False,
                'error': message,
                'rate_limited': rate_limited,
                'previous': previous,
            }

        if not new_letter:
            return {
                'draft': draft,
                'ok': False,
                'error': 'AI returned an empty cover letter.',
                'rate_limited': False,
                'previous': previous,
            }

        draft.cover_letter = new_letter
        return {
            'draft': draft,
            'ok': True,
            'error': None,
            'rate_limited': False,
        }

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
