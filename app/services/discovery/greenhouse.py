"""Greenhouse discovery: company Job Board API + optional MyGreenhouse search."""

import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlparse

import requests

from app.services.discovery.base import DiscoveredJobDTO, DiscoverySearchError

logger = logging.getLogger(__name__)

MY_GREENHOUSE_MARKERS = (
    'my.greenhouse.io',
    'mygreenhouse',
)
MY_GREENHOUSE_TOKEN = 'my'


class GreenhouseConnector:
    source_name = 'greenhouse'
    API_BASE = 'https://boards-api.greenhouse.io/v1/boards'
    TIMEOUT = 15

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        boards = profile_data.get('greenhouse_boards') or []
        titles = profile_data.get('titles') or ['software engineer']
        results: List[DiscoveredJobDTO] = []

        my_entries, company_boards, rejected = self._partition_boards(boards)
        for bad in rejected:
            logger.warning(
                'Ignoring invalid Greenhouse board entry %r — use a company token '
                '(e.g. stripe) from boards.greenhouse.io/{token}, or "my" for MyGreenhouse.',
                bad,
            )

        if my_entries:
            results.extend(self._search_my_greenhouse(titles, limit, user_id))
            if len(results) >= limit:
                return results[:limit]

        if not company_boards and not my_entries:
            logger.warning(
                'Greenhouse source enabled but no valid boards configured. '
                'Add company board tokens (boards.greenhouse.io/stripe → "stripe") '
                'or "my" to search https://my.greenhouse.io/jobs (requires portal credentials).'
            )
            return []

        for board in company_boards:
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
                logger.warning('Greenhouse board fetch failed for %s: %s', board_token, exc)
                continue

            for job in jobs:
                title = job.get('title', '')
                if titles and not any(t.lower() in title.lower() for t in titles):
                    continue
                location = ''
                if job.get('location'):
                    location = (
                        job['location'].get('name', '')
                        if isinstance(job['location'], dict)
                        else str(job['location'])
                    )
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
    def _partition_boards(cls, boards: List[str]):
        my_entries: List[str] = []
        company: List[str] = []
        rejected: List[str] = []
        for raw in boards:
            board = (raw or '').strip()
            if not board:
                continue
            if cls._is_my_greenhouse(board):
                my_entries.append(board)
            elif cls._board_token(board):
                company.append(board)
            else:
                rejected.append(board)
        return my_entries, company, rejected

    @classmethod
    def _is_my_greenhouse(cls, board: str) -> bool:
        lower = (board or '').strip().lower()
        if lower in (MY_GREENHOUSE_TOKEN, 'mygreenhouse', 'my-greenhouse'):
            return True
        return any(marker in lower for marker in MY_GREENHOUSE_MARKERS)

    @classmethod
    def _board_token(cls, board: str) -> str:
        board = (board or '').strip()
        if not board or cls._is_my_greenhouse(board):
            return ''
        if 'greenhouse.io' in board.lower():
            parsed = urlparse(board if '://' in board else f'https://{board}')
            host = (parsed.hostname or '').lower()
            if host.startswith('my.') or host == 'my.greenhouse.io':
                return ''
            path = parsed.path.strip('/')
            if not path:
                return ''
            token = path.split('/')[0]
            # Reject mistaken path segments from MyGreenhouse-style URLs
            if token.lower() in ('jobs', 'job', 'login', 'users', 'api'):
                return ''
            return token
        # Plain token — reject reserved words
        if board.lower() in ('jobs', 'job', 'my', 'login'):
            return ''
        return board

    def _search_my_greenhouse(
        self,
        titles: List[str],
        limit: int,
        user_id,
    ) -> List[DiscoveredJobDTO]:
        """Search https://my.greenhouse.io/jobs?query=… with a logged-in session."""
        if os.getenv('GREENHOUSE_MY_SEARCH_ENABLED', 'true').lower() in ('false', '0', 'no'):
            logger.info('MyGreenhouse search disabled (GREENHOUSE_MY_SEARCH_ENABLED=false)')
            return []

        if not user_id:
            raise DiscoverySearchError(
                'MyGreenhouse search requires a logged-in user. '
                'Export a session with: python scripts/export_playwright_storage.py greenhouse'
            )

        from app.services.credential_vault_service import credential_vault_service
        from app.services.scraping.browser_manager import browser_manager
        from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus

        credentials = credential_vault_service.retrieve(user_id, 'greenhouse')
        if not credentials or not credentials.get('storage_state'):
            raise DiscoverySearchError(
                'MyGreenhouse requires portal credentials. '
                'Run: python scripts/export_playwright_storage.py greenhouse '
                'then paste the JSON at Portal Credentials (portal=greenhouse). '
                'Company boards still work without this — use tokens like "stripe" from '
                'boards.greenhouse.io/stripe.'
            )

        results: List[DiscoveredJobDTO] = []
        queries = [t for t in titles if t][:3] or ['software engineer']

        with browser_manager.session_page(
            'greenhouse', user_id, credentials, proof_name=f'{user_id}_my_gh'
        ) as page:
            if isinstance(page, ScrapeResult):
                raise DiscoverySearchError(
                    page.message or 'Could not open MyGreenhouse browser session'
                )

            for query in queries:
                if len(results) >= limit:
                    break
                batch = self._fetch_my_query(page, query, limit - len(results))
                if batch is None:
                    # Auth failure — stop early with clear message
                    raise DiscoverySearchError(
                        'MyGreenhouse session expired or login required. '
                        'Re-export storage_state and update Portal Credentials.'
                    )
                results.extend(batch)

        return results[:limit]

    def _fetch_my_query(self, page, query: str, limit: int) -> Optional[List[DiscoveredJobDTO]]:
        """Return jobs for one query, or None if auth is required."""
        from app.services.scraping.browser_manager import browser_manager

        api_url = f'https://my.greenhouse.io/jobs.json?query={quote_plus(query)}'
        try:
            resp = page.request.get(api_url, timeout=30000)
            if resp.status in (401, 403):
                return None
            if resp.ok:
                parsed = self._parse_jobs_json(resp.json(), limit)
                if parsed:
                    return parsed
        except Exception as exc:
            logger.debug('MyGreenhouse jobs.json failed: %s', exc)

        search_url = f'https://my.greenhouse.io/jobs?query={quote_plus(query)}'
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(2500)
        except Exception as exc:
            logger.warning('MyGreenhouse navigation failed: %s', exc)
            return []

        html = page.content() or ''
        issue = browser_manager.detect_page_issue(page, html, page.url)
        if issue and issue.status.value in ('auth_required', 'captcha', 'blocked'):
            return None

        lower = (page.url or '').lower()
        body = ''
        try:
            body = (page.inner_text('body') or '').lower()
        except Exception:
            pass
        if 'sign in' in body[:2000] or 'enter your email' in body[:2000] or 'security code' in body[:2000]:
            return None

        return self._parse_my_html(html, limit)

    @classmethod
    def _parse_jobs_json(cls, payload: Any, limit: int) -> List[DiscoveredJobDTO]:
        jobs_raw: List[dict] = []
        if isinstance(payload, list):
            jobs_raw = [j for j in payload if isinstance(j, dict)]
        elif isinstance(payload, dict):
            for key in ('jobs', 'results', 'job_posts', 'data'):
                val = payload.get(key)
                if isinstance(val, list):
                    jobs_raw = [j for j in val if isinstance(j, dict)]
                    break
            if not jobs_raw and payload.get('title') and payload.get('id'):
                jobs_raw = [payload]

        results: List[DiscoveredJobDTO] = []
        for job in jobs_raw:
            title = job.get('title') or job.get('name') or ''
            if not title:
                continue
            company = (
                (job.get('company') or {}).get('name')
                if isinstance(job.get('company'), dict)
                else job.get('company_name') or job.get('company') or 'Unknown'
            )
            url = (
                job.get('absolute_url')
                or job.get('url')
                or job.get('job_url')
                or job.get('public_url')
                or ''
            )
            location = ''
            loc = job.get('location')
            if isinstance(loc, dict):
                location = loc.get('name') or loc.get('display_name') or ''
            elif loc:
                location = str(loc)
            description = cls._strip_html(
                job.get('content') or job.get('description') or job.get('excerpt') or ''
            )
            results.append(DiscoveredJobDTO(
                title=title,
                company=str(company),
                description=description[:15000],
                url=url,
                source='greenhouse',
                source_id=str(job.get('id') or job.get('job_id') or url or title),
                location=location,
                raw_data=job,
            ))
            if len(results) >= limit:
                break
        return results

    @classmethod
    def _parse_my_html(cls, html: str, limit: int) -> List[DiscoveredJobDTO]:
        """Best-effort parse of MyGreenhouse HTML for job links."""
        results: List[DiscoveredJobDTO] = []
        # Prefer company board links when present
        patterns = [
            re.compile(
                r'href="(https?://boards\.greenhouse\.io/[^"]+/jobs/\d+[^"]*)"[^>]*>'
                r'(?:[^<]*<[^>]+>)*\s*([^<]{3,120})',
                re.I,
            ),
            re.compile(
                r'href="(https?://[^"]*greenhouse\.io[^"]*/jobs/\d+[^"]*)"[^>]*>'
                r'\s*([^<]{3,120})',
                re.I,
            ),
        ]
        seen = set()
        for pattern in patterns:
            for match in pattern.finditer(html or ''):
                url = match.group(1).split('?')[0]
                title = re.sub(r'\s+', ' ', match.group(2)).strip()
                if not title or url in seen:
                    continue
                seen.add(url)
                company = ''
                board_match = re.search(r'boards\.greenhouse\.io/([^/]+)/', url)
                if board_match:
                    company = board_match.group(1).replace('-', ' ').title()
                results.append(DiscoveredJobDTO(
                    title=title,
                    company=company or 'Greenhouse',
                    description='',
                    url=url,
                    source='greenhouse',
                    source_id=url.rsplit('/', 1)[-1],
                    location='',
                    raw_data={'url': url},
                ))
                if len(results) >= limit:
                    return results
        return results

    @classmethod
    def _strip_html(cls, html: str) -> str:
        text = re.sub(r'<[^>]+>', ' ', html or '')
        return re.sub(r'\s+', ' ', text).strip()
