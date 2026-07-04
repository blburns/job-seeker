"""Tests for scrape rate limiter Redis fallback."""

from unittest.mock import MagicMock, patch

from app.services.scraping.rate_limiter import ScrapeRateLimiter, scrape_rate_limiter


def test_acquire_lock_falls_back_when_redis_unreachable():
    ScrapeRateLimiter._redis_available = None
    ScrapeRateLimiter._redis_client = None

    mock_client = MagicMock()
    mock_client.ping.side_effect = ConnectionError('Error 61 connecting to localhost:6379')

    with patch.dict('os.environ', {'SCRAPE_USE_REDIS': 'auto', 'CELERY_BROKER_URL': 'redis://localhost:6379/0'}):
        with patch('redis.from_url', return_value=mock_client):
            import redis
            with patch.object(redis, 'from_url', return_value=mock_client):
                assert scrape_rate_limiter.acquire_lock('user-1', 'linkedin') is True
                assert scrape_rate_limiter.acquire_lock('user-1', 'linkedin') is False
                scrape_rate_limiter.release_lock('user-1', 'linkedin')
                assert scrape_rate_limiter.acquire_lock('user-1', 'linkedin') is True
