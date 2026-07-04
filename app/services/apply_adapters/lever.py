"""Lever apply adapter using Playwright."""

import logging
import os
import time

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)


class LeverAdapter:
    portal_name = 'lever'

    def can_handle(self, url: str) -> bool:
        return 'lever.co' in (url or '').lower() or 'jobs.lever' in (url or '').lower()

    def submit(self, context: ApplyContext) -> ApplyResult:
        if os.getenv('APPLY_AUTOMATION_ENABLED', 'false').lower() != 'true':
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Apply automation disabled.',
            )
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return ApplyResult(success=False, status='needs_manual', message='Playwright not installed')

        proof_dir = os.path.join('instance', 'submission_proofs')
        os.makedirs(proof_dir, exist_ok=True)
        proof_path = os.path.join(proof_dir, f'{context.application_id}_lever.png')

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true')
                page = browser.new_page()
                page.goto(context.job_url, timeout=30000)
                time.sleep(2)
                fields = context.form_fields
                for selector, value in [
                    ('input[name="name"]', fields.get('full_name', '')),
                    ('input[name="email"]', fields.get('email', '')),
                    ('input[name="phone"]', fields.get('phone', '')),
                ]:
                    if value:
                        try:
                            page.locator(selector).fill(str(value))
                        except Exception:
                            pass
                page.screenshot(path=proof_path)
                browser.close()
            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Lever form pre-filled; review and submit manually.',
                proof_path=proof_path,
            )
        except Exception as exc:
            logger.exception('Lever apply failed')
            return ApplyResult(success=False, status='failed', message=str(exc))
