"""Tests for LinkedIn HTML parser."""

from pathlib import Path

from app.services.scraping.parsers.linkedin_parser import build_search_url, parse_search_results

FIXTURE = Path(__file__).parent / 'fixtures' / 'linkedin_search.html'


def test_parse_linkedin_fixture():
    html = FIXTURE.read_text()
    jobs = parse_search_results(html, limit=10)
    assert len(jobs) == 2
    assert jobs[0]['source_id'] == '1234567890'
    assert 'Engineer' in jobs[0]['title']
    assert jobs[0]['company'] == 'TechCo'


def test_build_linkedin_search_url():
    url = build_search_url('backend developer', location='NYC', remote=True)
    assert 'linkedin.com/jobs/search' in url
    assert 'keywords=' in url
    assert 'f_WT=2' in url
