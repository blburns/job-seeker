"""Portal session health checks."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.services.credential_vault_service import credential_vault_service
from app.services.scraping.browser_manager import browser_manager
from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus

logger = logging.getLogger(__name__)

PORTAL_CHECK_URLS = {
    'linkedin': 'https://www.linkedin.com/feed/',
    'indeed': 'https://www.indeed.com/',
    'greenhouse': 'https://my.greenhouse.io/jobs?query=software',
}

# How long a successful session check is considered valid for UI display.
SESSION_VALIDITY = timedelta(days=7)

REAUTH_HINTS = {
    ScrapeStatus.AUTH_REQUIRED: (
        'Session expired or logged out. Re-export Playwright storage_state '
        'and replace the credential at Portal Credentials.'
    ),
    ScrapeStatus.CAPTCHA: (
        'Security checkpoint detected. Complete verification in a headed browser, '
        're-export storage_state, and update Portal Credentials.'
    ),
    ScrapeStatus.BLOCKED: (
        'Portal blocked this session. Wait, try headed Chrome, then re-export '
        'and update Portal Credentials if needed.'
    ),
}

GREENHOUSE_REAUTH_STEPS = (
    '1) Delete the Greenhouse credential below. '
    '2) Run: PLAYWRIGHT_CHANNEL=chrome python scripts/export_playwright_storage.py greenhouse '
    '3) Complete email OTP login in the browser until you see the jobs search page. '
    '4) Paste the full JSON here and click Test Session again.'
)


class SessionHealthService:
    @classmethod
    def reauth_message(cls, portal: str, status: ScrapeStatus, detail: str = '') -> str:
        """User-facing guidance when scrape/auth fails."""
        hint = REAUTH_HINTS.get(status, 'Session check failed. Update Portal Credentials and retry.')
        label = {
            'linkedin': 'LinkedIn',
            'indeed': 'Indeed',
            'greenhouse': 'Greenhouse',
            'lever': 'Lever',
        }.get((portal or '').lower(), (portal or 'Portal').title())
        base = f'{label}: {hint}'
        if (portal or '').lower() == 'greenhouse':
            base = f'{base} {GREENHOUSE_REAUTH_STEPS}'
        if detail and detail not in base:
            return f'{base} ({detail})'
        return base

    @classmethod
    def check(cls, user_id, portal: str, credentials: Optional[Dict[str, Any]] = None) -> ScrapeResult:
        if credentials is None:
            credentials, error = credential_vault_service.retrieve_with_status(user_id, portal)
            if error == 'decrypt_failed':
                return ScrapeResult.failure(
                    ScrapeStatus.AUTH_REQUIRED,
                    'Stored credential cannot be decrypted. Set CREDENTIAL_ENCRYPTION_KEY in .env, '
                    'restart the app, delete the old credential, and paste your session JSON again.',
                )
            if error == 'not_found' or not credentials:
                if portal == 'linkedin':
                    return ScrapeResult.failure(
                        ScrapeStatus.AUTH_REQUIRED,
                        'No LinkedIn session stored. Export Playwright storage_state and add credentials.',
                    )
                if portal == 'indeed':
                    credentials = {}
                else:
                    return ScrapeResult.failure(
                        ScrapeStatus.AUTH_REQUIRED,
                        f'No {portal} session stored.',
                    )

        if portal in ('linkedin', 'greenhouse') and not credentials.get('storage_state'):
            return ScrapeResult.failure(
                ScrapeStatus.AUTH_REQUIRED,
                f'{portal.title()} credential is missing storage_state. '
                'Delete it and paste the full export JSON.',
            )

        url = PORTAL_CHECK_URLS.get(portal, '')
        if not url:
            return ScrapeResult.failure(ScrapeStatus.ERROR, f'Unknown portal: {portal}')

        result = browser_manager.fetch_html(url, portal, user_id, credentials)
        if result.ok:
            # Extra confirmation for MyGreenhouse: jobs.json should not 401
            if portal == 'greenhouse':
                json_ok = cls._probe_my_greenhouse_json(user_id, credentials)
                if json_ok is False:
                    return ScrapeResult.failure(
                        ScrapeStatus.AUTH_REQUIRED,
                        'MyGreenhouse cookies loaded a page but jobs.json still requires login.',
                    )
            return ScrapeResult.success(message='Session is valid', url=result.url)
        return result

    @classmethod
    def _probe_my_greenhouse_json(cls, user_id, credentials: Dict[str, Any]) -> Optional[bool]:
        """Return True if jobs.json OK, False if 401, None if probe skipped/failed."""
        try:
            with browser_manager.session_page(
                'greenhouse', user_id, credentials, proof_name=f'{user_id}_gh_probe'
            ) as page:
                from app.services.scraping.scrape_result import ScrapeResult as SR
                if isinstance(page, SR):
                    return False
                resp = page.request.get(
                    'https://my.greenhouse.io/jobs.json?query=software',
                    timeout=20000,
                )
                if resp.status in (401, 403):
                    return False
                if resp.ok:
                    return True
        except Exception as exc:
            logger.debug('MyGreenhouse JSON probe skipped: %s', exc)
        return None

    @classmethod
    def check_and_update_credential(cls, user_id, portal: str) -> ScrapeResult:
        from app.extensions.core import db
        from app.models.jobs import PortalCredential

        result = cls.check(user_id, portal)
        cred = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_active=True, is_deleted=False
        ).order_by(PortalCredential.created_at.desc()).first()
        if not cred:
            return result

        now = datetime.utcnow()
        if result.ok:
            cred.last_used_at = now
            cred.expires_at = now + SESSION_VALIDITY
            db.session.commit()
            return result

        if result.status in (
            ScrapeStatus.AUTH_REQUIRED, ScrapeStatus.CAPTCHA, ScrapeStatus.BLOCKED
        ):
            # Mark expired so the credentials UI prompts re-auth. Do not soft-delete.
            cred.expires_at = now
            db.session.commit()
            logger.warning(
                'Session check failed for %s (user=%s): %s',
                portal, user_id, result.message,
            )
            result.message = cls.reauth_message(portal, result.status, result.message)
        return result

    @classmethod
    def clear_health(cls, user_id, portal: str) -> bool:
        """Reset expires_at so UI shows Untested (after replacing a session)."""
        from app.extensions.core import db
        from app.models.jobs import PortalCredential

        cred = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_active=True, is_deleted=False
        ).order_by(PortalCredential.created_at.desc()).first()
        if not cred:
            return False
        cred.expires_at = None
        db.session.commit()
        return True

    @classmethod
    def credential_health_label(cls, cred) -> str:
        """UI label: healthy | expired | untested | inactive."""
        if not getattr(cred, 'is_active', True):
            return 'inactive'
        expires = getattr(cred, 'expires_at', None)
        if expires is None:
            return 'untested'
        if expires <= datetime.utcnow():
            return 'expired'
        return 'healthy'


session_health = SessionHealthService()
