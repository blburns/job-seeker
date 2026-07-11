"""Indeed apply adapter — pre-fill + proof; manual submit (ROADMAP D6)."""

import logging
import os
import time
from typing import Any, Optional

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)


class IndeedAdapter:
    """
    Opens the Indeed job page with a stored session, pre-fills common fields,
    captures a proof screenshot, and returns needs_manual.

    Full auto-submit is intentionally not attempted: Indeed often redirects to
    employer ATS sites and blocks headless automation.
    """

    portal_name = 'indeed'

    def can_handle(self, url: str) -> bool:
        return 'indeed.com' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if not context.portal_credentials or not context.portal_credentials.get('storage_state'):
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Indeed session not configured. Add portal credentials.',
                metadata={'job_url': context.job_url},
            )
        if os.getenv('INDEED_AUTO_APPLY_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Indeed auto-apply disabled. Enable INDEED_AUTO_APPLY_ENABLED for pre-fill assist.',
                metadata={'job_url': context.job_url},
            )
        if os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Apply automation disabled. Set APPLY_AUTOMATION_ENABLED=true.',
                metadata={'job_url': context.job_url},
            )
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError:
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Playwright not installed',
            )

        from app.services.proof_paths import submission_proof_path

        proof_path = submission_proof_path(str(context.application_id), 'indeed')

        try:
            from app.services.scraping.browser_manager import browser_manager

            with browser_manager.session_page(
                'indeed',
                context.user_id,
                context.portal_credentials,
                proof_name=f'apply_{context.application_id}',
            ) as page:
                from app.services.scraping.scrape_result import ScrapeResult

                if isinstance(page, ScrapeResult):
                    return ApplyResult(
                        success=False,
                        status='failed',
                        message=page.message or 'Browser session failed',
                        proof_path=page.proof_path or '',
                    )
                return self._run_on_page(page, context, proof_path)
        except Exception as exc:
            logger.exception('Indeed apply assist failed')
            return ApplyResult(success=False, status='failed', message=str(exc))

    def _run_on_page(self, page: Any, context: ApplyContext, proof_path: str) -> ApplyResult:
        page.goto(context.job_url, wait_until='domcontentloaded', timeout=45000)
        time.sleep(2.0)

        apply_opened = self._click_apply(page)
        time.sleep(1.5)
        filled = 0
        if apply_opened:
            filled = self._fill_common_fields(page, context.form_fields or {})
            self._upload_resume(page, context.resume_path)

        # Do not click final Submit — Indeed/employer flows are fragile (D6).
        confirmed = self.detect_confirmation(
            getattr(page, 'url', '') or '',
            self._page_text(page),
        )
        self._safe_screenshot(page, proof_path)
        proof = proof_path if os.path.exists(proof_path) else ''

        if confirmed:
            return ApplyResult(
                success=True,
                status='submitted',
                message='Indeed application confirmation detected.',
                proof_path=proof,
                metadata={'portal': self.portal_name, 'fields_filled': filled},
            )

        if apply_opened:
            message = (
                'Indeed apply form opened and pre-filled where possible. '
                'Finish and submit manually — auto-submit is not enabled for Indeed.'
            )
        else:
            message = (
                'Could not open an Indeed apply form (may redirect to employer site). '
                'Use the proof screenshot and apply manually.'
            )

        return ApplyResult(
            success=False,
            status='needs_manual',
            message=message,
            proof_path=proof,
            metadata={
                'portal': self.portal_name,
                'apply_opened': apply_opened,
                'fields_filled': filled,
            },
        )

    @classmethod
    def detect_confirmation(cls, url: str, body_text: str) -> bool:
        url_l = (url or '').lower()
        body_l = (body_text or '').lower()
        if any(token in url_l for token in ('confirmation', 'thank', 'applied', 'success')):
            return True
        phrases = (
            'application submitted',
            'application has been submitted',
            'thanks for applying',
            'thank you for applying',
            'we received your application',
        )
        return any(p in body_l for p in phrases)

    @classmethod
    def _click_apply(cls, page: Any) -> bool:
        selectors = (
            'button:has-text("Apply now")',
            'a:has-text("Apply now")',
            'button:has-text("Apply")',
            '[data-testid="indeedApplyButton"]',
            '#indeedApplyButton',
            'button.jobsearch-IndeedApplyButton',
        )
        for selector in selectors:
            try:
                loc = page.locator(selector).first
                if hasattr(loc, 'count') and loc.count() == 0:
                    continue
                loc.click(timeout=4000)
                return True
            except Exception:
                continue
        return False

    @classmethod
    def _fill_common_fields(cls, page: Any, fields: dict) -> int:
        full_name = (fields.get('full_name') or '').strip()
        parts = full_name.split()
        first = parts[0] if parts else ''
        last = ' '.join(parts[1:]) if len(parts) > 1 else ''
        mapping = [
            ('input[name="email"]', fields.get('email')),
            ('input[id*="email" i]', fields.get('email')),
            ('input[type="email"]', fields.get('email')),
            ('input[name="phone"]', fields.get('phone')),
            ('input[id*="phone" i]', fields.get('phone')),
            ('input[name="firstName"]', first),
            ('input[name="lastName"]', last),
            ('input[name="name"]', full_name),
        ]
        filled = 0
        for selector, value in mapping:
            if not value:
                continue
            try:
                page.locator(selector).first.fill(str(value), timeout=2000)
                filled += 1
            except Exception:
                continue
        return filled

    @classmethod
    def _upload_resume(cls, page: Any, resume_path: Optional[str]) -> None:
        if not resume_path or not os.path.exists(resume_path):
            return
        try:
            page.locator('input[type="file"]').first.set_input_files(resume_path)
        except Exception:
            logger.debug('Indeed resume upload skipped', exc_info=True)

    @classmethod
    def _page_text(cls, page: Any) -> str:
        try:
            return page.inner_text('body') or ''
        except Exception:
            return ''

    @classmethod
    def _safe_screenshot(cls, page: Any, proof_path: str) -> None:
        try:
            page.screenshot(path=proof_path, full_page=True)
        except Exception:
            logger.debug('Indeed proof screenshot failed', exc_info=True)
