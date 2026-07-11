"""Remotive connector tests with mocked HTTP."""

from unittest.mock import MagicMock, patch

from app.services.discovery.remotive import RemotiveConnector


@patch('app.services.discovery.remotive.requests.get')
def test_remotive_filters_by_title(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            'jobs': [
                {
                    'id': 1,
                    'title': 'Python Developer',
                    'company_name': 'Acme',
                    'description': 'Build APIs',
                    'url': 'https://remotive.com/remote-jobs/1',
                    'candidate_required_location': 'Worldwide',
                },
                {
                    'id': 2,
                    'title': 'Java Engineer',
                    'company_name': 'Other',
                    'description': 'JVM work',
                    'url': 'https://remotive.com/remote-jobs/2',
                    'candidate_required_location': 'USA',
                },
            ]
        },
    )
    results = RemotiveConnector().search({'titles': ['python']}, limit=10)
    assert len(results) == 1
    assert results[0].source == 'remotive'
    assert results[0].company == 'Acme'
    assert results[0].source_id == '1'
    assert results[0].title == 'Python Developer'


@patch('app.services.discovery.remotive.requests.get')
def test_remotive_returns_empty_on_http_error(mock_get):
    mock_get.side_effect = Exception('network down')
    assert RemotiveConnector().search({'titles': ['python']}) == []


@patch('app.services.discovery.remotive.requests.get')
def test_remotive_respects_limit(mock_get):
    jobs = [
        {
            'id': i,
            'title': f'Python Role {i}',
            'company_name': f'Co{i}',
            'description': 'x',
            'url': f'https://remotive.com/{i}',
            'candidate_required_location': 'Remote',
        }
        for i in range(10)
    ]
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {'jobs': jobs},
    )
    results = RemotiveConnector().search({'titles': ['python']}, limit=3)
    assert len(results) == 3
