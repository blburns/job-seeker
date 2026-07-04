"""Parse LinkedIn job search results HTML."""

import re
from typing import Any, Dict, List
from urllib.parse import quote_plus, urljoin

BASE_URL = 'https://www.linkedin.com'


def parse_search_results(html: str, limit: int = 50) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    seen_ids = set()

    chunks = re.split(r'class=["\']base-search-card["\']', html, flags=re.I)
    for chunk in chunks[1:]:
        link = re.search(r'href="(/jobs/view/[^"]+)"', chunk, re.I)
        if not link:
            continue
        href = link.group(1)
        job_id_match = re.search(r'/jobs/view/(?:[^/]+/)?(\d+)', href)
        if not job_id_match:
            continue
        job_id = job_id_match.group(1)
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        title = _extract(chunk, r'base-search-card__title[^"]*"[^>]*>([^<]+)')
        company = _extract(chunk, r'base-search-card__subtitle[^"]*"[^>]*>([^<]+)')
        location = _extract(chunk, r'job-search-card__location[^"]*"[^>]*>([^<]+)')
        jobs.append({
            'source_id': job_id,
            'title': title or 'Untitled',
            'company': company or 'Unknown',
            'location': location,
            'description': '',
            'url': urljoin(BASE_URL, href),
        })
        if len(jobs) >= limit:
            break

    if not jobs:
        for job_id in re.findall(r'/jobs/view/(?:[^"\']+/)?(\d+)', html):
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)
            jobs.append({
                'source_id': job_id,
                'title': 'Untitled',
                'company': 'Unknown',
                'location': '',
                'description': '',
                'url': urljoin(BASE_URL, f'/jobs/view/{job_id}'),
            })
            if len(jobs) >= limit:
                break

    return jobs[:limit]


def build_search_url(keywords: str, location: str = '', remote: bool = False) -> str:
    params = [f'keywords={quote_plus(keywords)}']
    if location:
        params.append(f'location={quote_plus(location)}')
    if remote:
        params.append('f_WT=2')
    return f'{BASE_URL}/jobs/search/?{"&".join(params)}'


def _extract(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.I | re.S)
    return _clean(m.group(1)) if m else ''


def _clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text or '')
    return re.sub(r'\s+', ' ', text).strip()
