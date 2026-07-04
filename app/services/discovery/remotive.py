"""Remotive public jobs API connector."""

import logging
from typing import Any, Dict, List

import requests

from app.services.discovery.base import DiscoveredJobDTO

logger = logging.getLogger(__name__)


class RemotiveConnector:
    source_name = 'remotive'
    API_URL = 'https://remotive.com/api/remote-jobs'
    TIMEOUT = 15

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        titles = [t.lower() for t in (profile_data.get('titles') or [])]
        keywords_include = [k.lower() for k in (profile_data.get('keywords_include') or [])]
        results: List[DiscoveredJobDTO] = []

        try:
            resp = requests.get(self.API_URL, timeout=self.TIMEOUT)
            resp.raise_for_status()
            jobs = resp.json().get('jobs', [])
        except Exception as exc:
            logger.warning('Remotive fetch failed: %s', exc)
            return []

        for job in jobs:
            title = job.get('title', '')
            title_lower = title.lower()
            if titles and not any(t in title_lower for t in titles):
                continue
            if keywords_include and not any(k in title_lower or k in (job.get('description', '').lower()) for k in keywords_include):
                continue
            results.append(DiscoveredJobDTO(
                title=title,
                company=job.get('company_name', 'Unknown'),
                description=(job.get('description') or '')[:15000],
                url=job.get('url', ''),
                source=self.source_name,
                source_id=str(job.get('id', '')),
                location=job.get('candidate_required_location', 'Remote'),
                raw_data=job,
            ))
            if len(results) >= limit:
                break
        return results
