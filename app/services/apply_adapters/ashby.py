"""Ashby apply adapter — needs_manual with pre-fill metadata."""

from app.services.apply_adapters.base import ApplyContext, ApplyResult


class AshbyAdapter:
    portal_name = 'ashby'

    def can_handle(self, url: str) -> bool:
        lower = (url or '').lower()
        return 'ashbyhq.com' in lower or 'jobs.ashbyhq.com' in lower

    def submit(self, context: ApplyContext) -> ApplyResult:
        return ApplyResult(
            success=False,
            status='needs_manual',
            message=(
                'Ashby applications are not auto-submitted. '
                'Use the pre-filled fields and apply on the Ashby careers page.'
            ),
            metadata={
                'job_url': context.job_url,
                'form_fields': context.form_fields,
                'portal': self.portal_name,
            },
        )
