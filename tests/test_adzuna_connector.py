"""Adzuna connector tests with mocked HTTP."""

from unittest.mock import MagicMock, patch

from app.services.discovery.adzuna import AdzunaConnector


def test_adzuna_returns_empty_without_credentials(monkeypatch):
    monkeypatch.delenv('ADZUNA_APP_ID', raising=False)
    monkeypatch.delenv('ADZUNA_APP_KEY', raising=False)
    assert AdzunaConnector().search({'titles': ['python']}) == []


@patch('app.services.discovery.adzuna.requests.get')
def test_adzuna_parses_results(mock_get, monkeypatch):
    monkeypatch.setenv('ADZUNA_APP_ID', 'id')
    monkeypatch.setenv('ADZUNA_APP_KEY', 'key')
    mock_get.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            'results': [
                {
                    'id': 99,
                    'title': 'Python Developer',
                    'company': {'display_name': 'Acme'},
                    'description': 'Build APIs',
                    'redirect_url': 'https://adzuna.example/job/99',
                    'location': {'display_name': 'Remote'},
                    'salary_min': 100000,
                    'salary_max': 140000,
                }
            ]
        },
    )
    results = AdzunaConnector().search({'titles': ['python'], 'locations': ['us']}, limit=5)
    assert len(results) == 1
    assert results[0].source == 'adzuna'
    assert results[0].company == 'Acme'
    assert results[0].salary_min == 100000
