"""Indeed apply adapter stub."""

import logging
import os

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)


class IndeedAdapter:
    portal_name = 'indeed'

    def can_handle(self, url: str) -> bool:
        return 'indeed.com' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if os.getenv('INDEED_AUTO_APPLY_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Indeed auto-apply disabled. Apply via company site or enable flag.',
                metadata={'job_url': context.job_url},
            )
        return ApplyResult(
            success=False,
            status='needs_manual',
            message='Indeed redirects to employer sites; manual apply recommended.',
            metadata={'job_url': context.job_url},
        )
