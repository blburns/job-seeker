"""LinkedIn Easy Apply adapter with session credentials."""

import logging
import os

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)


class LinkedInAdapter:
    portal_name = 'linkedin'

    def can_handle(self, url: str) -> bool:
        return 'linkedin.com' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if not context.portal_credentials:
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='LinkedIn session not configured. Add portal credentials.',
            )
        if os.getenv('LINKEDIN_AUTO_APPLY_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='LinkedIn auto-apply disabled. Enable LINKEDIN_AUTO_APPLY_ENABLED.',
                metadata={'job_url': context.job_url},
            )
        return ApplyResult(
            success=False,
            status='needs_manual',
            message='LinkedIn Easy Apply requires manual confirmation with stored session.',
            metadata={'job_url': context.job_url, 'form_fields': context.form_fields},
        )
