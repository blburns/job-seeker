"""Scrape rate limiter Redis mode tests."""

from unittest.mock import MagicMock

from app.services.scraping.rate_limiter import ScrapeRateLimiter


def test_redis_enabled_true(monkeypatch):
    monkeypatch.setenv('SCRAPE_USE_REDIS', 'true')
    assert ScrapeRateLimiter._redis_enabled() is True


def test_redis_enabled_auto_with_celery(monkeypatch):
    monkeypatch.setenv('SCRAPE_USE_REDIS', 'auto')
    monkeypatch.setenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    assert ScrapeRateLimiter._redis_enabled() is True


def test_redis_enabled_false(monkeypatch):
    monkeypatch.setenv('SCRAPE_USE_REDIS', 'false')
    monkeypatch.delenv('CELERY_BROKER_URL', raising=False)
    assert ScrapeRateLimiter._redis_enabled() is False


def test_hourly_cap_uses_redis_when_available(monkeypatch):
    monkeypatch.setenv('SCRAPE_USE_REDIS', 'true')
    ScrapeRateLimiter._redis_client = None
    ScrapeRateLimiter._redis_available = None

    fake = MagicMock()
    fake.get.return_value = '25'
    monkeypatch.setattr(ScrapeRateLimiter, '_get_redis', classmethod(lambda cls: fake))
    ScrapeRateLimiter.HOURLY_CAP = 20
    msg = ScrapeRateLimiter.check_hourly_cap('user-1', 'linkedin')
    assert msg is not None
    assert 'Hourly scrape cap' in msg
    fake.get.assert_called()
