"""Generic fallback adapter — marks needs_manual with pre-fill data."""

from app.services.apply_adapters.base import ApplyContext, ApplyResult


class GenericAdapter:
    portal_name = 'generic'

    def can_handle(self, url: str) -> bool:
        return True

    def submit(self, context: ApplyContext) -> ApplyResult:
        return ApplyResult(
            success=False,
            status='needs_manual',
            message='No automated adapter for this portal. Use pre-fill and apply manually.',
            metadata={'job_url': context.job_url, 'form_fields': context.form_fields},
        )
