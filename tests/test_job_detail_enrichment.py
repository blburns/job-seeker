"""Tests for job detail enrichment retry behavior."""

from types import SimpleNamespace
from unittest.mock import patch

from app.services.scraping.job_detail_enrichment import JobDetailEnrichment
from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus


def test_enrichment_retries_playwright_fetch():
    discovered = SimpleNamespace(
        title='Engineer',
        company='Acme',
        location='Remote',
        description='short',
        url='https://www.linkedin.com/jobs/view/1',
        source='linkedin',
    )
    calls = {'n': 0}

    def once(*_a, **_k):
        calls['n'] += 1
        if calls['n'] == 1:
            return None
        return {'description': 'A' * 500, 'title': 'Engineer', 'company': 'Acme'}

    with patch.object(JobDetailEnrichment, '_fetch_playwright_once', side_effect=once):
        with patch(
            'app.services.scraping.job_detail_enrichment.credential_vault_service.retrieve',
            return_value={},
        ):
            result = JobDetailEnrichment._fetch_with_playwright(discovered, 'user-1')
    assert calls['n'] == 2
    assert result and len(result['description']) >= 400


def test_enrichment_returns_none_after_exhausted_retries():
    discovered = SimpleNamespace(
        title='Engineer',
        company='Acme',
        location='',
        description='',
        url='https://www.indeed.com/viewjob?jk=1',
        source='indeed',
    )
    with patch.object(JobDetailEnrichment, '_fetch_playwright_once', return_value=None):
        with patch(
            'app.services.scraping.job_detail_enrichment.credential_vault_service.retrieve',
            return_value={},
        ):
            assert JobDetailEnrichment._fetch_with_playwright(discovered, 'user-1') is None


def test_enrich_discovered_keeps_partial_on_failure():
    discovered = SimpleNamespace(
        title='Engineer',
        company='Acme',
        location='Remote',
        description='partial blurb',
        url='https://www.linkedin.com/jobs/view/1',
        source='linkedin',
    )
    with patch.object(JobDetailEnrichment, '_fetch_with_playwright', return_value=None):
        with patch(
            'app.services.scraping.job_detail_enrichment.job_discovery_service.fetch_from_url',
            side_effect=Exception('network'),
        ):
            result = JobDetailEnrichment.enrich_discovered_job(discovered, 'user-1')
    assert result['title'] == 'Engineer'
    assert result['company'] == 'Acme'
    assert result['description'] == 'partial blurb'
