"""Tests for discovery connectors with mocked responses."""

from unittest.mock import MagicMock, patch

from app.services.discovery.greenhouse import GreenhouseConnector
from app.services.discovery.lever import LeverConnector


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
    connector = GreenhouseConnector()
    results = connector.search(
        {'greenhouse_boards': ['acme'], 'titles': ['python engineer']},
        limit=10,
    )
    assert len(results) == 1
    assert results[0].source == 'greenhouse'
    assert 'Python' in results[0].title


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
    connector = LeverConnector()
    results = connector.search({'lever_boards': ['acme'], 'titles': []}, limit=10)
    assert len(results) == 1
    assert results[0].source == 'lever'
