"""Greenhouse apply adapter using Playwright."""

import logging
import os
import re
import time
from typing import Any, Optional

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)

# Confirmation signals after a successful Greenhouse application.
_CONFIRMATION_URL_HINTS = (
    'confirmation',
    'thank',
    'thanks',
    'submitted',
    'application_received',
)
_CONFIRMATION_TEXT_PATTERNS = (
    r'thank you for (?:your )?appl(?:y|ication)',
    r'application (?:has been |was )?submitted',
    r'we(?:\'ve| have) received your application',
    r'your application was sent',
    r'successfully applied',
)

_SUBMIT_SELECTORS = (
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit Application")',
    'button:has-text("Submit")',
    'input[value="Submit Application"]',
    'input[value="Submit"]',
    '#submit_app',
    '[data-qa="btn-submit"]',
)


class GreenhouseAdapter:
    portal_name = 'greenhouse'

    def can_handle(self, url: str) -> bool:
        return 'greenhouse.io' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Apply automation disabled. Set APPLY_AUTOMATION_ENABLED=true.',
            )
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Playwright not installed',
            )

        proof_dir = os.path.join('instance', 'submission_proofs')
        os.makedirs(proof_dir, exist_ok=True)
        proof_path = os.path.join(proof_dir, f'{context.application_id}.png')

        try:
            headless = os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                page = browser.new_page()
                try:
                    result = self._run_on_page(page, context, proof_path)
                finally:
                    browser.close()
            return result
        except Exception as exc:
            logger.exception('Greenhouse apply failed')
            return ApplyResult(success=False, status='failed', message=str(exc))

    def _run_on_page(self, page: Any, context: ApplyContext, proof_path: str) -> ApplyResult:
        page.goto(context.job_url, timeout=30000)
        time.sleep(1.5)
        self._fill_fields(page, context.form_fields or {})
        self._upload_resume(page, context.resume_path)

        clicked = self.click_submit(page)
        if not clicked:
            self._safe_screenshot(page, proof_path)
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Could not find Greenhouse Submit control; form may be pre-filled — finish manually.',
                proof_path=proof_path if os.path.exists(proof_path) else '',
            )

        time.sleep(2.0)
        confirmed = self.detect_confirmation(
            getattr(page, 'url', '') or '',
            self._page_text(page),
        )
        self._safe_screenshot(page, proof_path)

        if confirmed:
            return ApplyResult(
                success=True,
                status='submitted',
                message='Greenhouse application submitted.',
                proof_path=proof_path if os.path.exists(proof_path) else '',
                metadata={'portal': self.portal_name, 'submit_clicked': True},
            )

        return ApplyResult(
            success=False,
            status='needs_manual',
            message=(
                'Submit was clicked but confirmation was not detected. '
                'Review the proof screenshot and finish manually if needed.'
            ),
            proof_path=proof_path if os.path.exists(proof_path) else '',
            metadata={'portal': self.portal_name, 'submit_clicked': True, 'confirmed': False},
        )

    @classmethod
    def _fill_fields(cls, page: Any, fields: dict) -> None:
        full_name = (fields.get('full_name') or '').strip()
        parts = full_name.split() if full_name else []
        first = parts[0] if parts else ''
        last = ' '.join(parts[1:]) if len(parts) > 1 else ''
        for label, value in [
            ('First Name', first),
            ('Last Name', last),
            ('Email', fields.get('email', '')),
            ('Phone', fields.get('phone', '')),
        ]:
            if not value:
                continue
            try:
                page.get_by_label(label, exact=False).fill(str(value))
            except Exception:
                logger.debug('Could not fill Greenhouse field %s', label, exc_info=True)

    @classmethod
    def _upload_resume(cls, page: Any, resume_path: Optional[str]) -> None:
        if not resume_path or not os.path.exists(resume_path):
            return
        try:
            page.locator('input[type="file"]').first.set_input_files(resume_path)
        except Exception:
            logger.debug('Could not upload Greenhouse resume', exc_info=True)

    @classmethod
    def click_submit(cls, page: Any) -> bool:
        """Click the first matching Submit control. Returns True if a click succeeded."""
        for selector in _SUBMIT_SELECTORS:
            try:
                locator = page.locator(selector).first
                if hasattr(locator, 'count') and locator.count() == 0:
                    continue
                locator.click(timeout=3000)
                return True
            except Exception:
                continue
        # Fallback: role-based button
        try:
            page.get_by_role('button', name=re.compile(r'submit', re.I)).first.click(timeout=3000)
            return True
        except Exception:
            return False

    @classmethod
    def detect_confirmation(cls, page_url: str, page_text: str) -> bool:
        """Return True when URL or body text indicates a successful application."""
        url = (page_url or '').lower()
        if any(hint in url for hint in _CONFIRMATION_URL_HINTS):
            return True
        text = (page_text or '').lower()
        if not text:
            return False
        return any(re.search(pattern, text, re.I) for pattern in _CONFIRMATION_TEXT_PATTERNS)

    @classmethod
    def _page_text(cls, page: Any) -> str:
        try:
            return page.inner_text('body') or ''
        except Exception:
            try:
                return page.content() or ''
            except Exception:
                return ''

    @classmethod
    def _safe_screenshot(cls, page: Any, proof_path: str) -> None:
        try:
            page.screenshot(path=proof_path)
        except Exception:
            logger.debug('Greenhouse screenshot failed', exc_info=True)
