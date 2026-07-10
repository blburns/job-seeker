"""LinkedIn Easy Apply adapter with session credentials."""

import logging
import os
import re
import time
from typing import Any, Optional

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)

_NEXT_BUTTON_PATTERNS = (
    r'^next$',
    r'^review$',
    r'^submit application$',
    r'^submit$',
    r'^continue$',
)


class LinkedInAdapter:
    portal_name = 'linkedin'

    def can_handle(self, url: str) -> bool:
        return 'linkedin.com' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if not context.portal_credentials or not context.portal_credentials.get('storage_state'):
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
        if os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Apply automation disabled. Set APPLY_AUTOMATION_ENABLED=true.',
            )
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
        except ImportError:
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Playwright not installed',
            )

        proof_dir = os.path.join('instance', 'submission_proofs')
        os.makedirs(proof_dir, exist_ok=True)
        proof_path = os.path.join(proof_dir, f'{context.application_id}_linkedin.png')

        try:
            from app.services.scraping.browser_manager import browser_manager

            with browser_manager.session_page(
                'linkedin',
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
            logger.exception('LinkedIn Easy Apply failed')
            return ApplyResult(success=False, status='failed', message=str(exc))

    def _run_on_page(self, page: Any, context: ApplyContext, proof_path: str) -> ApplyResult:
        page.goto(context.job_url, wait_until='domcontentloaded', timeout=45000)
        time.sleep(2.0)

        if not self._click_easy_apply(page):
            self._safe_screenshot(page, proof_path)
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Easy Apply button not found — job may require external apply.',
                proof_path=proof_path if os.path.exists(proof_path) else '',
            )

        time.sleep(1.5)
        self._fill_common_fields(page, context.form_fields or {})
        self._upload_resume(page, context.resume_path)

        advanced = self._advance_modal(page, max_steps=6)
        time.sleep(1.5)
        confirmed = self.detect_confirmation(
            getattr(page, 'url', '') or '',
            self._page_text(page),
        )
        self._safe_screenshot(page, proof_path)

        if confirmed:
            return ApplyResult(
                success=True,
                status='submitted',
                message='LinkedIn Easy Apply submitted.',
                proof_path=proof_path if os.path.exists(proof_path) else '',
                metadata={'portal': self.portal_name, 'steps': advanced},
            )

        return ApplyResult(
            success=False,
            status='needs_manual',
            message=(
                'Easy Apply modal opened and fields were pre-filled where possible, '
                'but confirmation was not detected. Finish in the browser using the proof screenshot.'
            ),
            proof_path=proof_path if os.path.exists(proof_path) else '',
            metadata={'portal': self.portal_name, 'steps': advanced, 'confirmed': False},
        )

    @classmethod
    def _click_easy_apply(cls, page: Any) -> bool:
        selectors = (
            'button.jobs-apply-button',
            'button:has-text("Easy Apply")',
            'button:has-text("Apply")',
            '[data-control-name="jobdetails_topcard_inapply"]',
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
    def _fill_common_fields(cls, page: Any, fields: dict) -> None:
        full_name = (fields.get('full_name') or '').strip()
        parts = full_name.split()
        first = parts[0] if parts else ''
        last = ' '.join(parts[1:]) if len(parts) > 1 else ''
        mapping = [
            ('input[name="email"]', fields.get('email')),
            ('input[id*="email" i]', fields.get('email')),
            ('input[name="phoneNumber"]', fields.get('phone')),
            ('input[id*="phone" i]', fields.get('phone')),
            ('input[name="firstName"]', first),
            ('input[name="lastName"]', last),
        ]
        for selector, value in mapping:
            if not value:
                continue
            try:
                page.locator(selector).first.fill(str(value), timeout=2000)
            except Exception:
                continue

    @classmethod
    def _upload_resume(cls, page: Any, resume_path: Optional[str]) -> None:
        if not resume_path or not os.path.exists(resume_path):
            return
        try:
            page.locator('input[type="file"]').first.set_input_files(resume_path)
        except Exception:
            logger.debug('LinkedIn resume upload skipped', exc_info=True)

    @classmethod
    def _advance_modal(cls, page: Any, max_steps: int = 6) -> int:
        """Click through Next/Review/Submit up to max_steps. Returns steps taken."""
        steps = 0
        for _ in range(max_steps):
            clicked = False
            for pattern in _NEXT_BUTTON_PATTERNS:
                try:
                    btn = page.get_by_role('button', name=re.compile(pattern, re.I)).first
                    btn.click(timeout=2500)
                    clicked = True
                    steps += 1
                    time.sleep(1.0)
                    break
                except Exception:
                    continue
            if not clicked:
                break
            if cls.detect_confirmation(getattr(page, 'url', '') or '', cls._page_text(page)):
                break
        return steps

    @classmethod
    def detect_confirmation(cls, page_url: str, page_text: str) -> bool:
        url = (page_url or '').lower()
        if 'application-submitted' in url or '/applied' in url:
            return True
        text = (page_text or '').lower()
        if not text:
            return False
        # Prefer strong phrases over bare "applied"
        strong = (
            r'application (?:was |has been )?sent',
            r'your application was submitted',
            r'thank you for applying',
            r'application submitted',
        )
        return any(re.search(p, text, re.I) for p in strong)

    @classmethod
    def _page_text(cls, page: Any) -> str:
        try:
            return page.inner_text('body') or ''
        except Exception:
            return ''

    @classmethod
    def _safe_screenshot(cls, page: Any, proof_path: str) -> None:
        try:
            page.screenshot(path=proof_path)
        except Exception:
            logger.debug('LinkedIn screenshot failed', exc_info=True)
