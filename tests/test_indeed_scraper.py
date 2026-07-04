"""Tests for Indeed HTML parser."""

from pathlib import Path

from app.services.scraping.parsers.indeed_parser import build_search_url, parse_search_results

FIXTURE = Path(__file__).parent / 'fixtures' / 'indeed_search.html'


def test_parse_indeed_fixture():
    html = FIXTURE.read_text()
    jobs = parse_search_results(html, limit=10)
    assert len(jobs) == 2
    assert jobs[0]['source_id'] == 'abc123def456'
    assert 'Python' in jobs[0]['title']
    assert jobs[0]['company'] == 'Acme Corp'


def test_build_indeed_search_url():
    url = build_search_url('software engineer', location='', remote=True, max_age_days=7)
    assert 'indeed.com/jobs' in url
    assert 'software' in url
    assert 'fromage=7' in url
    assert 'l=remote' in url
