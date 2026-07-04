"""Portal session health checks."""

import logging
from typing import Any, Dict, Optional

from app.services.credential_vault_service import credential_vault_service
from app.services.scraping.browser_manager import browser_manager
from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus

logger = logging.getLogger(__name__)

PORTAL_CHECK_URLS = {
    'linkedin': 'https://www.linkedin.com/feed/',
    'indeed': 'https://www.indeed.com/',
}


class SessionHealthService:
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

        if portal == 'linkedin' and not credentials.get('storage_state'):
            return ScrapeResult.failure(
                ScrapeStatus.AUTH_REQUIRED,
                'LinkedIn credential is missing storage_state. Delete it and paste the full export JSON.',
            )

        url = PORTAL_CHECK_URLS.get(portal, '')
        if not url:
            return ScrapeResult.failure(ScrapeStatus.ERROR, f'Unknown portal: {portal}')

        result = browser_manager.fetch_html(url, portal, user_id, credentials)
        if result.ok:
            return ScrapeResult.success(message='Session is valid', url=result.url)
        return result

    @classmethod
    def check_and_update_credential(cls, user_id, portal: str) -> ScrapeResult:
        from app.extensions.core import db
        from app.models.jobs import PortalCredential

        result = cls.check(user_id, portal)
        cred = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_active=True, is_deleted=False
        ).order_by(PortalCredential.created_at.desc()).first()
        if cred and not result.ok and result.status in (
            ScrapeStatus.AUTH_REQUIRED, ScrapeStatus.CAPTCHA, ScrapeStatus.BLOCKED
        ):
            # Do not auto-deactivate — user can delete and re-add from credentials UI.
            logger.warning(
                'Session check failed for %s (user=%s): %s',
                portal, user_id, result.message,
            )
        return result


session_health = SessionHealthService()
