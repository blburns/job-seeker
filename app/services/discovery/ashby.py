"""Ashby public job board connector."""

import logging
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from app.services.discovery.base import DiscoveredJobDTO

logger = logging.getLogger(__name__)


class AshbyConnector:
    source_name = 'ashby'
    TIMEOUT = 15
    API_TMPL = 'https://api.ashbyhq.com/posting-api/job-board/{board}'

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        boards = profile_data.get('ashby_boards') or []
        titles = [t.lower() for t in (profile_data.get('titles') or [])]
        results: List[DiscoveredJobDTO] = []

        for board in boards:
            slug = self._board_slug(board)
            if not slug:
                continue
            try:
                resp = requests.get(
                    self.API_TMPL.format(board=slug),
                    params={'includeCompensation': 'true'},
                    timeout=self.TIMEOUT,
                )
                resp.raise_for_status()
                payload = resp.json() or {}
                jobs = payload.get('jobs') or []
            except Exception as exc:
                logger.warning('Ashby fetch failed for %s: %s', slug, exc)
                continue

            company_label = slug.replace('-', ' ').title()
            for job in jobs:
                if job.get('isListed') is False:
                    continue
                title = job.get('title', '') or ''
                if titles and not any(t in title.lower() for t in titles):
                    continue
                desc = self._strip_html(job.get('descriptionHtml') or job.get('descriptionPlain') or '')
                job_url = job.get('jobUrl') or job.get('applyUrl') or ''
                results.append(DiscoveredJobDTO(
                    title=title,
                    company=job.get('department') or company_label,
                    description=desc[:15000],
                    url=job_url,
                    source=self.source_name,
                    source_id=str(job.get('id') or job.get('jobId') or job_url),
                    location=job.get('location') or '',
                    raw_data=job,
                ))
                if len(results) >= limit:
                    return results
        return results

    @classmethod
    def _board_slug(cls, board: str) -> str:
        board = (board or '').strip()
        if not board:
            return ''
        if 'ashbyhq.com' in board:
            path = urlparse(board).path.strip('/')
            return path.split('/')[0] if path else ''
        return board

    @classmethod
    def _strip_html(cls, html: str) -> str:
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()
