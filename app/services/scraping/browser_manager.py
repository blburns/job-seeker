"""Playwright browser lifecycle for portal scraping."""

import logging
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from app.services.scraping.browser_launch_args import SCRAPE_BROWSER_ARGS
from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus

logger = logging.getLogger(__name__)

WARM_UP_URLS = {
    'linkedin': 'https://www.linkedin.com/feed/',
    'indeed': 'https://www.indeed.com/',
    'greenhouse': 'https://my.greenhouse.io/jobs',
}

# Phrases on visible challenge pages — not script bundle names like "recaptcha".
CAPTCHA_VISIBLE_PHRASES = (
    "let's do a quick security check",
    'quick security check',
    'security verification',
    'verify you are human',
    'unusual activity from your network',
    "we've detected automated behavior",
    'detected automated behavior',
    'please complete this security check',
)

BLOCKED_VISIBLE_PHRASES = (
    'unusual traffic',
    'access denied',
    '403 forbidden',
)


class BrowserManager:
    USER_AGENT = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    @classmethod
    def is_playwright_available(cls) -> bool:
        try:
            import playwright  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def _proof_dir(cls) -> str:
        from app.services.proof_paths import SCRAPE_PROOF_DIR, ensure_proof_dirs
        ensure_proof_dirs()
        return SCRAPE_PROOF_DIR

    @classmethod
    def screenshot(cls, page, name: str) -> str:
        from app.services.proof_paths import scrape_proof_path
        path = scrape_proof_path(name)
        try:
            page.screenshot(path=path, full_page=True)
        except Exception as exc:
            logger.warning('Screenshot failed: %s', exc)
        return path

    @classmethod
    def _visible_text(cls, page, html: str) -> str:
        try:
            return (page.inner_text('body') or '').lower()
        except Exception:
            return (html or '').lower()[:12000]

    @classmethod
    def _headless_for(cls, portal: str) -> bool:
        portal_key = f'{portal.upper()}_PLAYWRIGHT_HEADLESS'
        portal_override = os.getenv(portal_key, '').strip().lower()
        if portal_override in ('true', '1', 'yes'):
            return True
        if portal_override in ('false', '0', 'no'):
            return False
        # Indeed and MyGreenhouse often fail in headless Chromium.
        if portal in ('indeed', 'greenhouse'):
            return False
        return os.getenv('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'

    @classmethod
    def detect_page_issue(cls, page, html: str, url: str) -> Optional[ScrapeResult]:
        lower_url = (url or '').lower()

        title = ''
        try:
            title = (page.title() or '').lower()
        except Exception:
            pass
        visible = cls._visible_text(page, html)

        if 'indeed.com' in lower_url:
            if 'blocked - indeed' in title or 'additional verification required' in visible[:3000]:
                return ScrapeResult.failure(
                    ScrapeStatus.BLOCKED,
                    'Indeed blocked automated access. Use headed Chrome '
                    '(PLAYWRIGHT_HEADLESS=false, PLAYWRIGHT_CHANNEL=chrome).',
                    url=url,
                )

        if 'authwall' in lower_url or ('login' in lower_url and 'linkedin.com' in lower_url):
            return ScrapeResult.failure(ScrapeStatus.AUTH_REQUIRED, 'Login required', url=url)
        if 'my.greenhouse.io' in lower_url:
            login_wall = (
                'enter your email address to continue' in visible
                or 'send security code' in visible
                or ('sign in' in visible[:1500] and 'looking for your organization' in visible)
            )
            # Logged-in jobs UI usually has search/results chrome, not the email OTP gate.
            logged_in = any(
                marker in visible
                for marker in (
                    'saved jobs',
                    'job alerts',
                    'applications',
                    'filter by',
                    'sort by',
                )
            ) or ('/jobs' in lower_url and 'query=' in lower_url and not login_wall)
            if login_wall and not logged_in:
                return ScrapeResult.failure(
                    ScrapeStatus.AUTH_REQUIRED,
                    'MyGreenhouse login required — export a fresh session with '
                    'python scripts/export_playwright_storage.py greenhouse '
                    'and replace the credential.',
                    url=url,
                )
        if 'checkpoint' in lower_url or 'challenge' in lower_url:
            return ScrapeResult.failure(
                ScrapeStatus.CAPTCHA,
                'LinkedIn security checkpoint — open linkedin.com in Chrome, complete any '
                'verification, re-export your session, and try again.',
                url=url,
            )

        combined = f'{title}\n{visible[:10000]}'

        if any(phrase in combined for phrase in CAPTCHA_VISIBLE_PHRASES):
            return ScrapeResult.failure(
                ScrapeStatus.CAPTCHA,
                'LinkedIn security checkpoint — complete verification in a normal browser, '
                're-export storage_state, and try again.',
                url=url,
            )
        if any(phrase in combined for phrase in BLOCKED_VISIBLE_PHRASES):
            return ScrapeResult.failure(ScrapeStatus.BLOCKED, 'Access blocked', url=url)

        if 'linkedin.com' in lower_url and 'sign in' in visible[:5000] and 'feed' not in lower_url:
            if 'jobs' in lower_url and 'authwall' in (html or '').lower():
                return ScrapeResult.failure(
                    ScrapeStatus.AUTH_REQUIRED,
                    'LinkedIn session expired',
                    url=url,
                )
        return None

    @classmethod
    def _browser_launch_args(cls) -> List[str]:
        return list(SCRAPE_BROWSER_ARGS)

    @classmethod
    def _launch_browser(cls, playwright, portal: str = ''):
        channel = os.getenv('PLAYWRIGHT_CHANNEL', '').strip()
        headless = cls._headless_for(portal)
        launch_kwargs = {
            'headless': headless,
            'args': cls._browser_launch_args(),
        }
        channels_to_try = [ch for ch in (channel, 'chrome', '') if ch != '']
        channels_to_try.append(None)

        last_error = None
        for ch in channels_to_try:
            try:
                if ch:
                    logger.info(
                        'Launching Playwright browser channel=%s headless=%s gpu=disabled',
                        ch, headless,
                    )
                    return playwright.chromium.launch(channel=ch, **launch_kwargs)
                return playwright.chromium.launch(**launch_kwargs)
            except Exception as exc:
                last_error = exc
                logger.warning('Browser launch failed (channel=%s): %s', ch, exc)
        raise RuntimeError(f'Could not launch browser: {last_error}')

    @classmethod
    @contextmanager
    def session_page(
        cls,
        portal: str,
        user_id,
        credentials: Optional[Dict[str, Any]] = None,
        proof_name: str = 'scrape',
    ) -> Generator:
        """Yield a Playwright page with optional storage_state."""
        if not cls.is_playwright_available():
            yield ScrapeResult.failure(ScrapeStatus.ERROR, 'Playwright not installed')
            return

        from playwright.sync_api import sync_playwright

        storage_state = None
        temp_file = None
        if credentials:
            storage_state = credentials.get('storage_state')
            if isinstance(storage_state, str):
                import json
                storage_state = json.loads(storage_state)

        if storage_state:
            fd, temp_file = tempfile.mkstemp(suffix='.json')
            import json
            with os.fdopen(fd, 'w') as f:
                json.dump(storage_state, f)

        playwright = None
        browser = None
        page = None
        try:
            playwright = sync_playwright().start()
            browser = cls._launch_browser(playwright, portal)
            context_kwargs = {
                'user_agent': (credentials or {}).get('user_agent') or cls.USER_AGENT,
                'viewport': {'width': 1366, 'height': 900},
                'locale': 'en-US',
                'timezone_id': os.getenv('PLAYWRIGHT_TIMEZONE', 'America/New_York'),
            }
            if temp_file:
                context_kwargs['storage_state'] = temp_file
            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            page.set_default_timeout(30000)
            yield page
        except Exception as exc:
            logger.exception('Browser session failed for %s', portal)
            proof = ''
            if page:
                proof = cls.screenshot(page, f'{proof_name}_{portal}')
            yield ScrapeResult.failure(ScrapeStatus.ERROR, str(exc), proof_path=proof)
        finally:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)

    @classmethod
    def _warm_session(cls, page, portal: str, credentials: Optional[Dict[str, Any]]) -> None:
        warm_url = WARM_UP_URLS.get(portal)
        if not warm_url or not credentials:
            return
        try:
            page.goto(warm_url, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(2500)
        except Exception as exc:
            logger.debug('Session warm-up skipped for %s: %s', portal, exc)

    @classmethod
    def fetch_indeed_detail(
        cls,
        url: str,
        user_id,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> ScrapeResult:
        """Load an Indeed viewjob page and extract fields via DOM selectors."""
        from app.services.scraping.parsers.indeed_parser import extract_job_detail_from_page

        proof_name = f'{user_id}_indeed_detail'
        with cls.session_page('indeed', user_id, credentials, proof_name) as page:
            if isinstance(page, ScrapeResult):
                return page
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                try:
                    page.wait_for_selector(
                        '#jobDescriptionText, [data-testid="jobDescriptionText"], h1',
                        timeout=30000,
                    )
                except Exception:
                    pass
                page.wait_for_timeout(3000)
                html = page.content()
                issue = cls.detect_page_issue(page, html, page.url)
                if issue:
                    issue.proof_path = cls.screenshot(page, proof_name)
                    return issue
                detail = extract_job_detail_from_page(page)
                return ScrapeResult.success(html=html, url=page.url, detail=detail)
            except Exception as exc:
                proof = cls.screenshot(page, proof_name)
                return ScrapeResult.failure(
                    ScrapeStatus.ERROR, str(exc), proof_path=proof, url=url,
                )

    @classmethod
    def fetch_html(
        cls,
        url: str,
        portal: str,
        user_id,
        credentials: Optional[Dict[str, Any]] = None,
        wait_selector: str = '',
    ) -> ScrapeResult:
        proof_name = f'{user_id}_{portal}'
        with cls.session_page(portal, user_id, credentials, proof_name) as page:
            if isinstance(page, ScrapeResult):
                return page
            try:
                cls._warm_session(page, portal, credentials)
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=20000)
                    except Exception:
                        pass
                page.wait_for_timeout(1500)
                html = page.content()
                issue = cls.detect_page_issue(page, html, page.url)
                if issue:
                    issue.proof_path = cls.screenshot(page, proof_name)
                    return issue
                return ScrapeResult.success(html=html, url=page.url)
            except Exception as exc:
                proof = cls.screenshot(page, proof_name)
                return ScrapeResult.failure(ScrapeStatus.ERROR, str(exc), proof_path=proof, url=url)


browser_manager = BrowserManager()
