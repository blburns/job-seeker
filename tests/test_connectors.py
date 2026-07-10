"""Tests for discovery connectors with mocked responses."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.discovery.base import DiscoverySearchError
from app.services.discovery.greenhouse import GreenhouseConnector
from app.services.discovery.lever import LeverConnector


def test_greenhouse_board_token_from_company_url():
    assert GreenhouseConnector._board_token('https://boards.greenhouse.io/stripe/jobs/1') == 'stripe'
    assert GreenhouseConnector._board_token('stripe') == 'stripe'


def test_greenhouse_rejects_mygreenhouse_as_board_token():
    assert GreenhouseConnector._board_token('https://my.greenhouse.io/jobs?query=') == ''
    assert GreenhouseConnector._board_token('https://my.greenhouse.io/jobs?query=software') == ''
    assert GreenhouseConnector._board_token('jobs') == ''
    assert GreenhouseConnector._is_my_greenhouse('my') is True
    assert GreenhouseConnector._is_my_greenhouse('https://my.greenhouse.io/jobs?query=') is True


def test_partition_boards_separates_my_and_company():
    my, company, rejected = GreenhouseConnector._partition_boards([
        'stripe',
        'my',
        'https://my.greenhouse.io/jobs?query=',
        'jobs',
    ])
    assert my == ['my', 'https://my.greenhouse.io/jobs?query=']
    assert company == ['stripe']
    assert 'jobs' in rejected


@patch('app.services.discovery.greenhouse.requests.get')
def test_greenhouse_connector_filters_by_title(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            'jobs': [
                {
                    'id': 1,
                    'title': 'Senior Python Engineer',
                    'location': {'name': 'Remote'},
                    'absolute_url': 'https://boards.greenhouse.io/acme/jobs/1',
                    'content': 'Python Flask SQL',
                },
                {
                    'id': 2,
                    'title': 'Sales Manager',
                    'location': {'name': 'NYC'},
                    'absolute_url': 'https://boards.greenhouse.io/acme/jobs/2',
                    'content': 'Sales',
                },
            ]
        },
    )
    mock_get.return_value.raise_for_status = lambda: None
    connector = GreenhouseConnector()
    results = connector.search(
        {'greenhouse_boards': ['acme'], 'titles': ['python engineer']},
        limit=10,
    )
    assert len(results) == 1
    assert results[0].source == 'greenhouse'
    assert 'Python' in results[0].title


def test_my_greenhouse_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        'app.services.credential_vault_service.credential_vault_service.retrieve',
        lambda *a, **k: None,
    )
    with pytest.raises(DiscoverySearchError, match='Portal Credentials'):
        GreenhouseConnector().search(
            {'greenhouse_boards': ['my'], 'titles': ['engineer']},
            user_id='u1',
        )


def test_parse_jobs_json_list():
    payload = {
        'jobs': [
            {
                'id': 9,
                'title': 'Backend Engineer',
                'company': {'name': 'Acme'},
                'absolute_url': 'https://boards.greenhouse.io/acme/jobs/9',
                'location': {'name': 'Remote'},
                'content': '<p>Python</p>',
            }
        ]
    }
    results = GreenhouseConnector._parse_jobs_json(payload, limit=5)
    assert len(results) == 1
    assert results[0].company == 'Acme'
    assert 'Python' in results[0].description


@patch('app.services.discovery.lever.requests.get')
def test_lever_connector_parses_jobs(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: [
            {
                'id': 'abc',
                'text': 'Backend Developer',
                'categories': {'location': 'Remote', 'team': 'Engineering'},
                'hostedUrl': 'https://jobs.lever.co/acme/abc',
                'descriptionPlain': 'Python APIs',
            }
        ],
    )
    mock_get.return_value.raise_for_status = lambda: None
    connector = LeverConnector()
    results = connector.search({'lever_boards': ['acme'], 'titles': []}, limit=10)
    assert len(results) == 1
    assert results[0].source == 'lever'
