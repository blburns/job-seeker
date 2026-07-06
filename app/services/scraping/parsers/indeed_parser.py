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


INDEED_DETAIL_JS = """() => {
  const pick = (...sels) => {
    for (const sel of sels) {
      const el = document.querySelector(sel);
      if (el && el.innerText && el.innerText.trim()) return el.innerText.trim();
    }
    return '';
  };
  return {
    title: pick(
      '[data-testid="job-title"]',
      'h1.jobsearch-JobInfoHeader-title',
      'h1'
    ),
    company: pick(
      '[data-testid="inlineHeader-companyName"]',
      '[data-testid="company-name"]',
      '[data-testid="jobsearch-CompanyInfoContainer"]'
    ),
    location: pick(
      '[data-testid="inlineHeader-companyLocation"]',
      '[data-testid="job-location"]',
      '#jobLocationText',
      '[data-testid="jobsearch-JobInfoHeader-subtitle"]'
    ),
    description: pick(
      '#jobDescriptionText',
      '[data-testid="jobDescriptionText"]',
      '.jobsearch-JobComponent-description'
    ),
  };
}"""


def extract_job_detail_from_page(page) -> Dict[str, Any]:
    """Extract job fields from a loaded Indeed viewjob Playwright page."""
    raw = page.evaluate(INDEED_DETAIL_JS)
    return _detail_dict(
        title=(raw.get('title') or '').strip(),
        company=(raw.get('company') or '').strip(),
        location=(raw.get('location') or '').strip(),
        description=(raw.get('description') or '').strip(),
    )


def parse_job_detail(html: str) -> Dict[str, Any]:
    """Extract full job fields from an Indeed viewjob HTML snapshot."""
    title = _extract(html, r'data-testid=["\']job-title["\'][^>]*>([^<]+)')
    if not title:
        title = _extract(html, r'class="[^"]*jobsearch-JobInfoHeader-title[^"]*"[^>]*>([^<]+)')
    if not title:
        title = _extract(html, r'<h1[^>]*>([^<]+)')

    company = _extract(html, r'data-testid=["\']inlineHeader-companyName["\'][^>]*>([^<]+)')
    if not company:
        company = _extract(html, r'data-testid=["\']company-name["\'][^>]*>([^<]+)')
    if not company:
        company = _extract(html, r'class="[^"]*jobsearch-InlineCompanyRating[^"]*"[^>]*>.*?>([^<]+)')

    location = _extract(html, r'data-testid=["\']inlineHeader-companyLocation["\'][^>]*>([^<]+)')
    if not location:
        location = _extract(html, r'data-testid=["\']job-location["\'][^>]*>([^<]+)')
    if not location:
        location = _extract(html, r'class="[^"]*jobsearch-JobInfoHeader-subtitle[^"]*"[^>]*>([^<]+)')

    description = _extract_description(html)
    return _detail_dict(title, company, location, description)


def _detail_dict(title, company, location, description) -> Dict[str, Any]:
    from app.services.job_discovery_service import job_discovery_service
    seniority = job_discovery_service._detect_seniority(f'{title} {description}')
    return {
        'title': title,
        'company': company,
        'location': location,
        'description': description,
        'requirements': description,
        'seniority': seniority,
    }


def _extract_description(html: str) -> str:
    for marker_pattern in (
        r'id=["\']jobDescriptionText["\']',
        r'data-testid=["\']jobDescriptionText["\']',
        r'class="[^"]*jobsearch-JobComponent-description[^"]*"',
    ):
        match = re.search(marker_pattern, html, re.I)
        if not match:
            continue
        rest = html[match.end():]
        gt = rest.find('>')
        if gt < 0:
            continue
        chunk = rest[gt + 1:]
        end = re.search(r'</body>|</html>', chunk, re.I)
        if end:
            chunk = chunk[:end.start()]
        text = _clean(chunk)
        if len(text) > 40:
            return text[:20000]
    return ''


def _extract(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.I | re.S)
    return _clean(m.group(1)) if m else ''


def _clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text or '')
    return re.sub(r'\s+', ' ', text).strip()
