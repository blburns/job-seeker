"""Lever public job board connector."""

import logging
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from app.services.discovery.base import DiscoveredJobDTO

logger = logging.getLogger(__name__)


class LeverConnector:
    source_name = 'lever'
    TIMEOUT = 15

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        boards = profile_data.get('lever_boards') or []
        titles = [t.lower() for t in (profile_data.get('titles') or [])]
        results: List[DiscoveredJobDTO] = []

        for board in boards:
            company = self._company_slug(board)
            if not company:
                continue
            try:
                resp = requests.get(
                    f'https://api.lever.co/v0/postings/{company}',
                    params={'mode': 'json'},
                    timeout=self.TIMEOUT,
                )
                resp.raise_for_status()
                jobs = resp.json()
            except Exception as exc:
                logger.warning('Lever fetch failed for %s: %s', company, exc)
                continue

            for job in jobs:
                title = job.get('text', '')
                if titles and not any(t in title.lower() for t in titles):
                    continue
                desc = job.get('descriptionPlain', '') or self._strip_html(job.get('description', ''))
                results.append(DiscoveredJobDTO(
                    title=title,
                    company=job.get('categories', {}).get('team', company.replace('-', ' ').title()),
                    description=desc[:15000],
                    url=job.get('hostedUrl', ''),
                    source=self.source_name,
                    source_id=job.get('id', ''),
                    location=job.get('categories', {}).get('location', ''),
                    raw_data=job,
                ))
                if len(results) >= limit:
                    return results
        return results

    @classmethod
    def _company_slug(cls, board: str) -> str:
        board = board.strip()
        if 'lever.co' in board:
            path = urlparse(board).path.strip('/')
            return path.split('/')[0] if path else ''
        return board

    @classmethod
    def _strip_html(cls, html: str) -> str:
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()
