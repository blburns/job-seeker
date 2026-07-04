"""Greenhouse apply adapter using Playwright."""

import logging
import os
import time

from app.services.apply_adapters.base import ApplyContext, ApplyResult

logger = logging.getLogger(__name__)


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
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true')
                page = browser.new_page()
                page.goto(context.job_url, timeout=30000)
                time.sleep(2)

                fields = context.form_fields
                for label, value in [
                    ('First Name', fields.get('full_name', '').split()[0] if fields.get('full_name') else ''),
                    ('Last Name', ' '.join(fields.get('full_name', '').split()[1:])),
                    ('Email', fields.get('email', '')),
                    ('Phone', fields.get('phone', '')),
                ]:
                    if value:
                        try:
                            page.get_by_label(label, exact=False).fill(str(value))
                        except Exception:
                            pass

                if context.resume_path and os.path.exists(context.resume_path):
                    try:
                        page.locator('input[type="file"]').first.set_input_files(context.resume_path)
                    except Exception:
                        pass

                page.screenshot(path=proof_path)
                browser.close()

            return ApplyResult(
                success=False,
                status='needs_manual',
                message='Greenhouse form pre-filled; review and submit manually.',
                proof_path=proof_path,
            )
        except Exception as exc:
            logger.exception('Greenhouse apply failed')
            return ApplyResult(success=False, status='failed', message=str(exc))
