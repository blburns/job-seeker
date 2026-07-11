"""RSS connector tests with mocked feed fetch."""

from unittest.mock import patch

from app.services.discovery.rss_connector import RssConnector


def test_rss_returns_empty_without_feeds():
    assert RssConnector().search({'titles': ['python']}) == []


@patch('app.services.discovery.rss_connector.job_discovery_service.search_rss_feed')
def test_rss_filters_by_title(mock_feed):
    mock_feed.return_value = [
        {
            'title': 'Senior Python Engineer',
            'company': 'FeedCo',
            'description': 'Remote Python role',
            'url': 'https://example.com/jobs/1',
        },
        {
            'title': 'Java Architect',
            'company': 'Other',
            'description': 'JVM',
            'url': 'https://example.com/jobs/2',
        },
    ]
    results = RssConnector().search(
        {'rss_feeds': ['https://example.com/feed.xml'], 'titles': ['python']},
        limit=10,
    )
    assert len(results) == 1
    assert results[0].source == 'rss'
    assert results[0].company == 'FeedCo'
    assert results[0].url == 'https://example.com/jobs/1'
    mock_feed.assert_called_once_with('https://example.com/feed.xml', limit=10)


@patch('app.services.discovery.rss_connector.job_discovery_service.search_rss_feed')
def test_rss_skips_failed_feeds(mock_feed):
    mock_feed.side_effect = Exception('bad xml')
    results = RssConnector().search(
        {'rss_feeds': ['https://example.com/broken.xml'], 'titles': ['python']},
    )
    assert results == []
