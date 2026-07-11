"""Tests for LinkedIn/Indeed discovery connectors with mocked browser fetches."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.discovery.base import DiscoverySearchError
from app.services.discovery.indeed import IndeedConnector
from app.services.discovery.linkedin import LinkedInConnector
from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.fixture(autouse=True)
def _enable_scrape_flags(monkeypatch):
    monkeypatch.setenv('LINKEDIN_SCRAPE_ENABLED', 'true')
    monkeypatch.setenv('INDEED_SCRAPE_ENABLED', 'true')
    # Avoid real delays in tests
    monkeypatch.setattr(
        'app.services.scraping.rate_limiter.scrape_rate_limiter.random_delay',
        lambda: None,
    )
    monkeypatch.setattr(
        'app.services.scraping.rate_limiter.scrape_rate_limiter.check_hourly_cap',
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        'app.services.scraping.rate_limiter.scrape_rate_limiter.acquire_lock',
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        'app.services.scraping.rate_limiter.scrape_rate_limiter.release_lock',
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        'app.services.scraping.rate_limiter.scrape_rate_limiter.record_run',
        lambda *a, **k: None,
    )


def test_linkedin_connector_disabled_raises(monkeypatch):
    monkeypatch.setenv('LINKEDIN_SCRAPE_ENABLED', 'false')
    with pytest.raises(DiscoverySearchError, match='LINKEDIN_SCRAPE_ENABLED'):
        LinkedInConnector().search({'titles': ['engineer']}, user_id='u1')


def test_linkedin_connector_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        'app.services.discovery.linkedin.credential_vault_service.retrieve',
        lambda *a, **k: None,
    )
    with pytest.raises(DiscoverySearchError, match='session not configured'):
        LinkedInConnector().search({'titles': ['engineer']}, user_id='u1')


@patch('app.services.discovery.linkedin.browser_manager.fetch_html')
def test_linkedin_connector_parses_fixture(mock_fetch, monkeypatch):
    html = (FIXTURES / 'linkedin_search.html').read_text()
    mock_fetch.return_value = ScrapeResult.success(html=html, url='https://www.linkedin.com/jobs/search/')
    monkeypatch.setattr(
        'app.services.discovery.linkedin.credential_vault_service.retrieve',
        lambda *a, **k: {'storage_state': {'cookies': [{'name': 'li_at', 'value': 'x'}], 'origins': []}},
    )
    results = LinkedInConnector().search(
        {'titles': ['software engineer'], 'locations': ['Remote']},
        limit=10,
        user_id='u1',
    )
    assert len(results) >= 1
    assert results[0].source == 'linkedin'
    assert results[0].title
    assert results[0].company


@patch('app.services.discovery.linkedin.browser_manager.fetch_html')
def test_linkedin_connector_auth_error_is_actionable(mock_fetch, monkeypatch):
    mock_fetch.return_value = ScrapeResult.failure(
        ScrapeStatus.AUTH_REQUIRED, 'Login required'
    )
    monkeypatch.setattr(
        'app.services.discovery.linkedin.credential_vault_service.retrieve',
        lambda *a, **k: {'storage_state': {'cookies': [{'name': 'li_at', 'value': 'x'}], 'origins': []}},
    )
    with pytest.raises(DiscoverySearchError, match='Portal Credentials'):
        LinkedInConnector().search({'titles': ['engineer']}, user_id='u1')


def test_indeed_connector_disabled_raises(monkeypatch):
    monkeypatch.setenv('INDEED_SCRAPE_ENABLED', 'false')
    with pytest.raises(DiscoverySearchError, match='INDEED_SCRAPE_ENABLED'):
        IndeedConnector().search({'titles': ['python']}, user_id='u1')


@patch('app.services.discovery.indeed.browser_manager.fetch_html')
def test_indeed_connector_parses_fixture(mock_fetch, monkeypatch):
    html = (FIXTURES / 'indeed_search.html').read_text()
    mock_fetch.return_value = ScrapeResult.success(html=html, url='https://www.indeed.com/jobs')
    monkeypatch.setattr(
        'app.services.discovery.indeed.credential_vault_service.retrieve',
        lambda *a, **k: None,
    )
    results = IndeedConnector().search(
        {'titles': ['python'], 'locations': ['Remote']},
        limit=10,
        user_id='u1',
    )
    assert len(results) >= 1
    assert results[0].source == 'indeed'


@patch('app.services.discovery.indeed.browser_manager.fetch_html')
def test_indeed_connector_retries_once_on_block(mock_fetch, monkeypatch):
    blocked = ScrapeResult.failure(ScrapeStatus.BLOCKED, 'Indeed blocked')
    html = (FIXTURES / 'indeed_search.html').read_text()
    ok = ScrapeResult.success(html=html, url='https://www.indeed.com/jobs')
    mock_fetch.side_effect = [blocked, ok]
    monkeypatch.setattr(
        'app.services.discovery.indeed.credential_vault_service.retrieve',
        lambda *a, **k: None,
    )
    results = IndeedConnector().search({'titles': ['python']}, limit=5, user_id='u1')
    assert mock_fetch.call_count == 2
    assert len(results) >= 1
