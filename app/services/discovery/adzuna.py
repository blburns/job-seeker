"""Adzuna job search API connector."""

import logging
import os
from typing import Any, Dict, List

import requests

from app.services.discovery.base import DiscoveredJobDTO

logger = logging.getLogger(__name__)


class AdzunaConnector:
    source_name = 'adzuna'
    TIMEOUT = 15

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        app_id = os.getenv('ADZUNA_APP_ID', '')
        app_key = os.getenv('ADZUNA_APP_KEY', '')
        if not app_id or not app_key:
            logger.info('Adzuna credentials not configured')
            return []

        titles = profile_data.get('titles') or ['software engineer']
        locations = profile_data.get('locations') or ['us']
        results: List[DiscoveredJobDTO] = []

        for title in titles[:3]:
            for location in locations[:2]:
                try:
                    country = 'us' if len(location) <= 3 else location.lower()[:2]
                    resp = requests.get(
                        f'https://api.adzuna.com/v1/api/jobs/{country}/search/1',
                        params={
                            'app_id': app_id,
                            'app_key': app_key,
                            'results_per_page': min(limit, 50),
                            'what': title,
                            'where': location,
                        },
                        timeout=self.TIMEOUT,
                    )
                    resp.raise_for_status()
                    jobs = resp.json().get('results', [])
                except Exception as exc:
                    logger.warning('Adzuna search failed: %s', exc)
                    continue

                for job in jobs:
                    results.append(DiscoveredJobDTO(
                        title=job.get('title', ''),
                        company=job.get('company', {}).get('display_name', 'Unknown'),
                        description=(job.get('description') or '')[:15000],
                        url=job.get('redirect_url', ''),
                        source=self.source_name,
                        source_id=str(job.get('id', '')),
                        location=job.get('location', {}).get('display_name', ''),
                        salary_min=job.get('salary_min'),
                        salary_max=job.get('salary_max'),
                        raw_data=job,
                    ))
                    if len(results) >= limit:
                        return results
        return results
