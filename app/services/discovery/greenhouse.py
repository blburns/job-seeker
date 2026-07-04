"""Greenhouse public board API connector."""

import logging
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from app.services.discovery.base import DiscoveredJobDTO
from app.services.keyword_service import keyword_service

logger = logging.getLogger(__name__)


class GreenhouseConnector:
    source_name = 'greenhouse'
    API_BASE = 'https://boards-api.greenhouse.io/v1/boards'
    TIMEOUT = 15

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        boards = profile_data.get('greenhouse_boards') or []
        titles = [t.lower() for t in (profile_data.get('titles') or [])]
        results: List[DiscoveredJobDTO] = []

        for board in boards:
            board_token = self._board_token(board)
            if not board_token:
                continue
            try:
                resp = requests.get(
                    f'{self.API_BASE}/{board_token}/jobs',
                    params={'content': 'true'},
                    timeout=self.TIMEOUT,
                )
                resp.raise_for_status()
                jobs = resp.json().get('jobs', [])
            except Exception as exc:
                logger.warning('Greenhouse fetch failed for %s: %s', board_token, exc)
                continue

            for job in jobs:
                title = job.get('title', '')
                if titles and not any(t in title.lower() for t in titles):
                    continue
                location = ''
                if job.get('location'):
                    location = job['location'].get('name', '') if isinstance(job['location'], dict) else str(job['location'])
                content = job.get('content', '') or ''
                company = board_token.replace('-', ' ').title()
                results.append(DiscoveredJobDTO(
                    title=title,
                    company=company,
                    description=self._strip_html(content)[:15000],
                    url=job.get('absolute_url', ''),
                    source=self.source_name,
                    source_id=str(job.get('id', '')),
                    location=location,
                    raw_data=job,
                ))
                if len(results) >= limit:
                    return results
        return results

    @classmethod
    def _board_token(cls, board: str) -> str:
        board = board.strip()
        if 'greenhouse.io' in board:
            path = urlparse(board).path.strip('/')
            return path.split('/')[0] if path else ''
        return board

    @classmethod
    def _strip_html(cls, html: str) -> str:
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()
