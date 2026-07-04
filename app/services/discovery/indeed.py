"""Indeed job discovery via Playwright scraping."""

import logging
import os
from typing import Any, Dict, List, Optional

from app.services.credential_vault_service import credential_vault_service
from app.services.discovery.base import DiscoveredJobDTO, DiscoverySearchError
from app.services.scraping.browser_manager import browser_manager
from app.services.scraping.parsers.indeed_parser import build_search_url, parse_search_results
from app.services.scraping.rate_limiter import scrape_rate_limiter
from app.services.scraping.scrape_result import ScrapeStatus

logger = logging.getLogger(__name__)


class IndeedConnector:
    source_name = 'indeed'

    def search(
        self,
        profile_data: Dict[str, Any],
        limit: int = 50,
        user_id=None,
    ) -> List[DiscoveredJobDTO]:
        if os.getenv('INDEED_SCRAPE_ENABLED', 'false').lower() != 'true':
            logger.info('Indeed scraping disabled (INDEED_SCRAPE_ENABLED=false)')
            return []

        if not user_id:
            raise DiscoverySearchError('user_id required for Indeed scraping')

        cap_error = scrape_rate_limiter.check_hourly_cap(user_id, self.source_name)
        if cap_error:
            raise DiscoverySearchError(cap_error)

        if not scrape_rate_limiter.acquire_lock(user_id, self.source_name):
            raise DiscoverySearchError('Indeed scrape already in progress for this account')

        try:
            titles = profile_data.get('titles') or ['software engineer']
            locations = profile_data.get('locations') or ['']
            remote = profile_data.get('remote_preference') in ('remote', 'any')
            max_age = int(profile_data.get('indeed_max_age_days') or 7)
            radius = int(profile_data.get('indeed_radius_miles') or 0)

            credentials = credential_vault_service.retrieve(user_id, self.source_name)
            results: List[DiscoveredJobDTO] = []

            for title in titles[:3]:
                for location in (locations[:2] or ['']):
                    if len(results) >= limit:
                        break
                    url = build_search_url(
                        title,
                        location=location,
                        remote=remote and not location,
                        max_age_days=max_age,
                        radius_miles=radius,
                    )
                    scrape_rate_limiter.random_delay()
                    fetch = browser_manager.fetch_html(
                        url, self.source_name, user_id, credentials,
                        wait_selector='[data-jk], .job_seen_beacon',
                    )
                    if not fetch.ok:
                        if fetch.status == ScrapeStatus.DISABLED:
                            return []
                        raise DiscoverySearchError(fetch.message)

                    for job in parse_search_results(fetch.html, limit=limit - len(results)):
                        results.append(DiscoveredJobDTO(
                            title=job['title'],
                            company=job['company'],
                            description=job.get('description', ''),
                            location=job.get('location', ''),
                            url=job['url'],
                            source=self.source_name,
                            source_id=job['source_id'],
                            raw_data=job,
                        ))

            scrape_rate_limiter.record_run(user_id, self.source_name)
            return results[:limit]
        finally:
            scrape_rate_limiter.release_lock(user_id, self.source_name)
