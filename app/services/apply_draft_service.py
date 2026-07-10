"""Create and validate apply pre-fill drafts."""

import logging
import os
import time
from typing import Any, Dict, Optional

from app.extensions.core import db
from app.models.jobs import ApplyDraft, MasterProfile
from app.services.job_discovery_service import job_discovery_service
from app.services.tailoring_service import tailoring_service

logger = logging.getLogger(__name__)


def _is_rate_limit_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return '429' in message or 'rate limit' in message or 'quota' in message


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
    def _retry_settings(cls) -> tuple:
        """Max attempts and base backoff seconds for free-tier rate limits."""
        try:
            max_attempts = max(1, int(os.getenv('COVER_LETTER_RETRY_MAX', '6')))
        except ValueError:
            max_attempts = 6
        try:
            base_seconds = max(1.0, float(os.getenv('COVER_LETTER_RETRY_BASE_SECONDS', '20')))
        except ValueError:
            base_seconds = 20.0
        return max_attempts, base_seconds

    @classmethod
    def regenerate_cover_letter(
        cls,
        application,
        user_id,
        *,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Regenerate cover letter with automatic retries on rate limits.

        Returns dict: {draft, ok, error, rate_limited, attempts, retried}
        """
        draft = cls.ensure_draft(application, user_id, profile_data=profile_data)
        if not draft:
            return {
                'draft': None,
                'ok': False,
                'error': 'No draft available — upload a master profile first.',
                'rate_limited': False,
                'attempts': 0,
                'retried': False,
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
                'attempts': 0,
                'retried': False,
            }

        letter_profile = profile_data or profile.profile_data or {}
        previous = draft.cover_letter or ''
        max_attempts, base_seconds = cls._retry_settings()
        last_error = ''
        hit_rate_limit = False
        retried = False

        for attempt in range(1, max_attempts + 1):
            try:
                new_letter = (cls._generate_cover_letter(job, letter_profile) or '').strip()
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    'Cover letter regeneration failed (attempt %s/%s): %s',
                    attempt,
                    max_attempts,
                    exc,
                )
                if _is_rate_limit_error(exc) and attempt < max_attempts:
                    hit_rate_limit = True
                    retried = True
                    # Exponential backoff: 20s, 40s, 80s… capped at 2 minutes
                    delay = min(base_seconds * (2 ** (attempt - 1)), 120.0)
                    logger.info(
                        'Rate limited — retrying cover letter in %.0fs (attempt %s/%s)',
                        delay,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(delay)
                    continue
                return {
                    'draft': draft,
                    'ok': False,
                    'error': last_error,
                    'rate_limited': _is_rate_limit_error(exc),
                    'previous': previous,
                    'attempts': attempt,
                    'retried': retried,
                }

            if not new_letter:
                last_error = 'AI returned an empty cover letter.'
                if attempt < max_attempts:
                    retried = True
                    delay = min(base_seconds * (2 ** (attempt - 1)), 120.0)
                    time.sleep(delay)
                    continue
                return {
                    'draft': draft,
                    'ok': False,
                    'error': last_error,
                    'rate_limited': hit_rate_limit,
                    'previous': previous,
                    'attempts': attempt,
                    'retried': retried,
                }

            draft.cover_letter = new_letter
            return {
                'draft': draft,
                'ok': True,
                'error': None,
                'rate_limited': False,
                'attempts': attempt,
                'retried': retried,
            }

        return {
            'draft': draft,
            'ok': False,
            'error': last_error or 'Cover letter regeneration failed after retries.',
            'rate_limited': hit_rate_limit,
            'previous': previous,
            'attempts': max_attempts,
            'retried': retried,
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
