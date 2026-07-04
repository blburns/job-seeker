"""Parse Indeed search results HTML."""

import re
from typing import Any, Dict, List
from urllib.parse import quote_plus, urljoin

BASE_URL = 'https://www.indeed.com'


def parse_search_results(html: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Extract job cards from Indeed search HTML."""
    jobs: List[Dict[str, Any]] = []
    seen_ids = set()

    job_ids = re.findall(r'data-jk=["\']([a-zA-Z0-9]+)["\']', html, re.I)
    if not job_ids:
        return []

    chunks = re.split(r'data-jk=["\']([a-zA-Z0-9]+)["\']', html, flags=re.I)
    # split returns [before, id1, chunk1, id2, chunk2, ...]
    for idx in range(1, len(chunks), 2):
        if idx + 1 >= len(chunks):
            break
        job_id = chunks[idx]
        chunk = chunks[idx + 1]
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        title = _extract_title(chunk, job_id)
        company = _extract(chunk, r'data-testid=["\']company-name["\'][^>]*>([^<]+)')
        if not company:
            company = _extract(chunk, r'class="[^"]*companyName[^"]*"[^>]*>(?:<span[^>]*>)?([^<]+)')
        location = _extract(chunk, r'data-testid=["\']text-location["\'][^>]*>([^<]+)')
        if not location:
            location = _extract(chunk, r'class="[^"]*companyLocation[^"]*"[^>]*>([^<]+)')
        snippet = _extract(chunk, r'class="[^"]*job-snippet[^"]*"[^>]*>([^<]+)')
        if not snippet:
            snippet = _extract(chunk, r'data-testid=["\']job-snippet["\'][^>]*>([^<]+)')

        jobs.append(_job_dict(
            job_id, title, company, location, snippet,
            urljoin(BASE_URL, f'/viewjob?jk={job_id}'),
        ))
        if len(jobs) >= limit:
            break

    return jobs[:limit]


def _extract_title(chunk: str, job_id: str) -> str:
    title = _extract(chunk, rf'id=["\']jobTitle-{re.escape(job_id)}["\'][^>]*>([^<]+)')
    if not title:
        title = _extract(chunk, r'title=["\']([^"\']+)["\']')
    if not title:
        title = _extract(chunk, r'class="[^"]*jobTitle[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>')
    if not title:
        title = _extract(chunk, r'<span[^>]*>([^<]+)</span>')
    return title


def build_search_url(
    query: str,
    location: str = '',
    remote: bool = False,
    max_age_days: int = 7,
    radius_miles: int = 0,
) -> str:
    params = [f'q={quote_plus(query)}']
    loc = (location or '').strip()
    if loc:
        params.append(f'l={quote_plus(loc)}')
    elif remote:
        params.append('l=remote')
    if remote and loc:
        params.append('sc=0kf%3Aattr(DSQF7)%3B')
    if max_age_days:
        params.append(f'fromage={max_age_days}')
    if radius_miles:
        params.append(f'radius={radius_miles}')
    return f'{BASE_URL}/jobs?{"&".join(params)}'


def _job_dict(job_id, title, company, location, description, url) -> Dict[str, Any]:
    return {
        'source_id': job_id,
        'title': title or 'Untitled',
        'company': company or 'Unknown',
        'location': location,
        'description': description,
        'url': url,
    }


def _extract(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.I | re.S)
    return _clean(m.group(1)) if m else ''


def _clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text or '')
    return re.sub(r'\s+', ' ', text).strip()
