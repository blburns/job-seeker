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
            # Cover letter is a dedicated column — strip legacy form_fields copy.
            fields = dict(draft.form_fields or {})
            if 'cover_letter' in fields:
                fields.pop('cover_letter', None)
                draft.form_fields = fields
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
        """
        Retry policy for free-tier rate limits.

        max_attempts: 0 = keep going until success or wall-clock timeout
        base_seconds: delay between retries (capped)
        timeout_seconds: safety stop so the request cannot hang forever
        """
        try:
            max_attempts = int(os.getenv('COVER_LETTER_RETRY_MAX', '0'))
        except ValueError:
            max_attempts = 0
        try:
            base_seconds = max(1.0, float(os.getenv('COVER_LETTER_RETRY_BASE_SECONDS', '30')))
        except ValueError:
            base_seconds = 30.0
        try:
            timeout_seconds = max(
                60.0,
                float(os.getenv('COVER_LETTER_RETRY_TIMEOUT_SECONDS', '1800')),
            )
        except ValueError:
            timeout_seconds = 1800.0
        return max_attempts, base_seconds, timeout_seconds

    @classmethod
    def regenerate_cover_letter(
        cls,
        application,
        user_id,
        *,
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Regenerate cover letter, keeping retrying on rate limits until success
        (or until COVER_LETTER_RETRY_TIMEOUT_SECONDS elapses).

        Returns dict: {draft, ok, error, rate_limited, attempts, retried, timed_out}
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
                'timed_out': False,
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
                'timed_out': False,
            }

        letter_profile = profile_data or profile.profile_data or {}
        previous = draft.cover_letter or ''
        max_attempts, base_seconds, timeout_seconds = cls._retry_settings()
        unlimited = max_attempts <= 0
        last_error = ''
        hit_rate_limit = False
        retried = False
        started = time.monotonic()
        attempt = 0

        while True:
            attempt += 1
            try:
                new_letter = (cls._generate_cover_letter(job, letter_profile) or '').strip()
            except Exception as exc:
                last_error = str(exc)
                rate_limited = _is_rate_limit_error(exc)
                logger.warning(
                    'Cover letter regeneration failed (attempt %s): %s',
                    attempt,
                    exc,
                )
                if rate_limited:
                    hit_rate_limit = True
                    retried = True
                    elapsed = time.monotonic() - started
                    if elapsed >= timeout_seconds:
                        return {
                            'draft': draft,
                            'ok': False,
                            'error': last_error,
                            'rate_limited': True,
                            'previous': previous,
                            'attempts': attempt,
                            'retried': retried,
                            'timed_out': True,
                        }
                    if not unlimited and attempt >= max_attempts:
                        return {
                            'draft': draft,
                            'ok': False,
                            'error': last_error,
                            'rate_limited': True,
                            'previous': previous,
                            'attempts': attempt,
                            'retried': retried,
                            'timed_out': False,
                        }
                    # Steady backoff for free tier; cap at 90s between tries
                    delay = min(base_seconds, 90.0)
                    remaining = timeout_seconds - elapsed
                    delay = min(delay, max(1.0, remaining))
                    logger.info(
                        'Rate limited — retrying cover letter in %.0fs '
                        '(attempt %s, %.0fs remaining)',
                        delay,
                        attempt + 1,
                        remaining,
                    )
                    time.sleep(delay)
                    continue

                # Non-rate-limit errors: fail immediately
                return {
                    'draft': draft,
                    'ok': False,
                    'error': last_error,
                    'rate_limited': False,
                    'previous': previous,
                    'attempts': attempt,
                    'retried': retried,
                    'timed_out': False,
                }

            if not new_letter:
                last_error = 'AI returned an empty cover letter.'
                retried = True
                elapsed = time.monotonic() - started
                if elapsed >= timeout_seconds or (not unlimited and attempt >= max_attempts):
                    return {
                        'draft': draft,
                        'ok': False,
                        'error': last_error,
                        'rate_limited': hit_rate_limit,
                        'previous': previous,
                        'attempts': attempt,
                        'retried': retried,
                        'timed_out': elapsed >= timeout_seconds,
                    }
                delay = min(base_seconds, 90.0)
                time.sleep(delay)
                continue

            draft.cover_letter = new_letter
            return {
                'draft': draft,
                'ok': True,
                'error': None,
                'rate_limited': False,
                'attempts': attempt,
                'retried': retried,
                'timed_out': False,
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
