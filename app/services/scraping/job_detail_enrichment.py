"""Fetch full job descriptions when list-scrape data is incomplete."""

import logging
from typing import Any, Dict, Optional

from app.services.credential_vault_service import credential_vault_service
from app.services.job_discovery_service import job_discovery_service
from app.services.scraping.browser_manager import browser_manager
from app.services.scraping.parsers.indeed_parser import parse_job_detail as parse_indeed_detail
from app.services.scraping.parsers.linkedin_parser import parse_job_detail as parse_linkedin_detail

logger = logging.getLogger(__name__)

PLAYWRIGHT_SOURCES = frozenset({'indeed', 'linkedin'})
MIN_DESCRIPTION_LEN = 80
FULL_DESCRIPTION_LEN = 400


class JobDetailEnrichment:
    @classmethod
    def keyword_text(cls, *, title='', company='', location='', description='', requirements='') -> str:
        return ' '.join(
            part for part in (title, company, location, description, requirements) if part
        ).strip()

    @classmethod
    def posting_keyword_text(cls, posting) -> str:
        return cls.keyword_text(
            title=posting.title,
            company=posting.company,
            location=posting.location,
            description=posting.description or '',
            requirements=posting.requirements or '',
        )

    @classmethod
    def needs_enrichment(cls, discovered) -> bool:
        description = (discovered.description or '').strip()
        if discovered.source in PLAYWRIGHT_SOURCES and (discovered.url or '').strip():
            return len(description) < FULL_DESCRIPTION_LEN
        company = (discovered.company or '').strip()
        return (
            len(description) < MIN_DESCRIPTION_LEN
            or company in ('', 'Unknown', 'Unknown Company')
            or not (discovered.location or '').strip()
        )

    @classmethod
    def needs_posting_enrichment(cls, posting) -> bool:
        if not (posting.url or '').strip():
            return False
        description = (posting.description or '').strip()
        if posting.source in PLAYWRIGHT_SOURCES:
            return len(description) < FULL_DESCRIPTION_LEN
        return len(description) < MIN_DESCRIPTION_LEN

    @classmethod
    def enrich_discovered_job(cls, discovered, user_id) -> Dict[str, Any]:
        base = {
            'title': discovered.title,
            'company': discovered.company,
            'location': discovered.location,
            'description': discovered.description or '',
            'requirements': '',
            'seniority': '',
        }
        if not cls.needs_enrichment(discovered):
            return base

        if discovered.source in PLAYWRIGHT_SOURCES and discovered.url:
            enriched = cls._fetch_with_playwright(discovered, user_id)
            if enriched:
                return cls._merge(base, enriched)

        if discovered.url:
            try:
                fetched = job_discovery_service.fetch_from_url(discovered.url)
                return cls._merge(base, fetched)
            except Exception as exc:
                logger.warning('URL fetch enrichment failed for %s: %s', discovered.url, exc)

        return base

    @classmethod
    def enrich_job_posting(cls, posting, user_id) -> bool:
        """Fetch missing portal detail into an existing posting."""
        if not cls.needs_posting_enrichment(posting):
            return False

        stub = type('_EnrichStub', (), {})()
        stub.title = posting.title
        stub.company = posting.company
        stub.location = posting.location
        stub.description = posting.description or ''
        stub.url = posting.url
        stub.source = posting.source

        enriched = cls.enrich_discovered_job(stub, user_id)
        return cls.apply_enrichment_to_posting(posting, enriched)

    @classmethod
    def apply_enrichment_to_posting(cls, posting, enriched: Dict[str, Any]) -> bool:
        changed = False
        for key in ('title', 'company', 'location', 'description', 'requirements', 'seniority'):
            new_val = (enriched.get(key) or '').strip()
            if not new_val:
                continue
            old_val = (getattr(posting, key, None) or '').strip()
            if key == 'description':
                if len(new_val) <= len(old_val):
                    continue
            elif key == 'company':
                if old_val and old_val not in ('Unknown', 'Unknown Company'):
                    continue
            elif key in ('location', 'title') and old_val:
                continue
            setattr(posting, key, new_val)
            changed = True
        return changed

    @classmethod
    def _fetch_with_playwright(cls, discovered, user_id) -> Optional[Dict[str, Any]]:
        credentials = credential_vault_service.retrieve(user_id, discovered.source)
        attempts = 2
        last_error = ''

        for attempt in range(1, attempts + 1):
            try:
                detail = cls._fetch_playwright_once(discovered, user_id, credentials)
                if detail:
                    return detail
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    'Detail enrichment attempt %s/%s failed for %s: %s',
                    attempt, attempts, discovered.url, exc,
                )
            if attempt < attempts:
                logger.info('Retrying job detail enrichment for %s', discovered.url)

        if last_error:
            logger.warning(
                'Detail enrichment exhausted retries for %s (%s); returning partial data',
                discovered.url, last_error,
            )
        return None

    @classmethod
    def _fetch_playwright_once(cls, discovered, user_id, credentials) -> Optional[Dict[str, Any]]:
        if discovered.source == 'indeed':
            fetch = browser_manager.fetch_indeed_detail(
                discovered.url, user_id, credentials,
            )
            if not fetch.ok:
                logger.warning(
                    'Indeed detail fetch failed (%s): %s',
                    discovered.url, fetch.message,
                )
                return None
            detail = fetch.metadata.get('detail')
            if detail and detail.get('description'):
                return detail
            if fetch.html:
                parsed = parse_indeed_detail(fetch.html)
                if parsed.get('description'):
                    return parsed
            # Partial: title/company without full description still useful
            if detail:
                return detail
            return None

        wait_selector = '.description__text, .show-more-less-html__markup'
        fetch = browser_manager.fetch_html(
            discovered.url,
            discovered.source,
            user_id,
            credentials,
            wait_selector=wait_selector,
        )
        if not fetch.ok:
            logger.warning(
                'Detail fetch failed for %s (%s): %s',
                discovered.source, discovered.url, fetch.message,
            )
            return None

        if discovered.source == 'linkedin':
            return parse_linkedin_detail(fetch.html)
        return None

    @classmethod
    def _merge(cls, base: Dict[str, Any], enriched: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base)
        for key in ('title', 'company', 'location', 'description', 'requirements', 'seniority'):
            new_val = (enriched.get(key) or '').strip()
            if not new_val:
                continue
            old_val = (out.get(key) or '').strip()
            if key == 'description':
                if len(new_val) > len(old_val):
                    out[key] = new_val
                continue
            if key == 'company' and old_val and old_val not in ('Unknown', 'Unknown Company'):
                continue
            if key in ('location', 'title') and old_val:
                continue
            out[key] = new_val
        return out


job_detail_enrichment = JobDetailEnrichment()
