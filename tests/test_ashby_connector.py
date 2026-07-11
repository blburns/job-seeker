"""Ashby discovery connector tests with mocked HTTP."""

from unittest.mock import MagicMock, patch

from app.services.discovery.ashby import AshbyConnector


@patch('app.services.discovery.ashby.requests.get')
def test_ashby_filters_by_title(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            'jobs': [
                {
                    'id': 'a1',
                    'title': 'Senior Python Engineer',
                    'department': 'Engineering',
                    'descriptionPlain': 'Build APIs',
                    'jobUrl': 'https://jobs.ashbyhq.com/acme/a1',
                    'location': 'Remote',
                    'isListed': True,
                },
                {
                    'id': 'a2',
                    'title': 'Sales Manager',
                    'department': 'Sales',
                    'descriptionPlain': 'Sell stuff',
                    'jobUrl': 'https://jobs.ashbyhq.com/acme/a2',
                    'location': 'NYC',
                    'isListed': True,
                },
            ]
        },
    )
    results = AshbyConnector().search(
        {'ashby_boards': ['acme'], 'titles': ['python']},
        limit=10,
    )
    assert len(results) == 1
    assert results[0].source == 'ashby'
    assert results[0].source_id == 'a1'
    assert results[0].title == 'Senior Python Engineer'
    assert 'ashbyhq.com' in results[0].url


@patch('app.services.discovery.ashby.requests.get')
def test_ashby_skips_unlisted(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            'jobs': [
                {
                    'id': 'hidden',
                    'title': 'Python Role',
                    'descriptionPlain': 'x',
                    'jobUrl': 'https://jobs.ashbyhq.com/acme/hidden',
                    'isListed': False,
                },
            ]
        },
    )
    assert AshbyConnector().search({'ashby_boards': ['acme'], 'titles': ['python']}) == []


@patch('app.services.discovery.ashby.requests.get')
def test_ashby_returns_empty_on_http_error(mock_get):
    mock_get.side_effect = Exception('network down')
    assert AshbyConnector().search({'ashby_boards': ['acme'], 'titles': ['python']}) == []


def test_ashby_board_slug_from_url():
    assert AshbyConnector._board_slug('https://jobs.ashbyhq.com/ramp/jobs') == 'ramp'
    assert AshbyConnector._board_slug('plaid') == 'plaid'
    assert AshbyConnector._board_slug('') == ''


@patch('app.services.discovery.ashby.requests.get')
def test_ashby_respects_limit(mock_get):
    jobs = [
        {
            'id': str(i),
            'title': f'Python Role {i}',
            'descriptionPlain': 'x',
            'jobUrl': f'https://jobs.ashbyhq.com/acme/{i}',
            'isListed': True,
        }
        for i in range(10)
    ]
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {'jobs': jobs},
    )
    results = AshbyConnector().search(
        {'ashby_boards': ['acme'], 'titles': ['python']},
        limit=3,
    )
    assert len(results) == 3
