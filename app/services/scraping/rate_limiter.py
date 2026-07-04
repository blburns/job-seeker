"""Per-user per-portal scrape rate limiting."""

import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

# In-process fallback when Redis unavailable
_memory_last_run: dict = {}
_memory_locks: set = set()
_memory_hourly_counts: dict = {}


class ScrapeRateLimiter:
    HOURLY_CAP = int(os.getenv('SCRAPE_RATE_LIMIT_PER_HOUR', '20'))
    DELAY_MIN_MS = int(os.getenv('SCRAPE_DELAY_MIN_MS', '2000'))
    DELAY_MAX_MS = int(os.getenv('SCRAPE_DELAY_MAX_MS', '6000'))

    _redis_client = None
    _redis_available: Optional[bool] = None

    @classmethod
    def _redis_enabled(cls) -> bool:
        mode = os.getenv('SCRAPE_USE_REDIS', 'false').lower()
        if mode in ('false', '0', 'no', 'off'):
            return False
        if mode in ('true', '1', 'yes', 'on'):
            return True
        # auto: try Redis when explicitly configured for Celery/Docker deployments
        return bool(os.getenv('CELERY_BROKER_URL', '').strip())

    @classmethod
    def _get_redis(cls):
        if not cls._redis_enabled():
            return None
        if cls._redis_available is False:
            return None
        if cls._redis_client is not None:
            return cls._redis_client
        try:
            import redis
            url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            cls._redis_client = client
            cls._redis_available = True
            return client
        except Exception as exc:
            cls._redis_available = False
            cls._redis_client = None
            logger.warning(
                'Redis unavailable for scrape rate limiting (%s); using in-memory fallback',
                exc,
            )
            return None

    @classmethod
    def _redis_call(cls, redis_fn: Callable, memory_fn: Callable[[], T]) -> T:
        client = cls._get_redis()
        if not client:
            return memory_fn()
        try:
            return redis_fn(client)
        except Exception as exc:
            cls._redis_available = False
            cls._redis_client = None
            logger.warning('Redis scrape limiter error (%s); using in-memory fallback', exc)
            return memory_fn()

    @classmethod
    def _key(cls, user_id, portal: str, suffix: str) -> str:
        return f'scrape:{user_id}:{portal}:{suffix}'

    @classmethod
    def acquire_lock(cls, user_id, portal: str, ttl_seconds: int = 600) -> bool:
        lock_key = cls._key(user_id, portal, 'lock')

        def memory_acquire() -> bool:
            if lock_key in _memory_locks:
                return False
            _memory_locks.add(lock_key)
            return True

        return cls._redis_call(
            lambda r: bool(r.set(lock_key, '1', nx=True, ex=ttl_seconds)),
            memory_acquire,
        )

    @classmethod
    def release_lock(cls, user_id, portal: str):
        lock_key = cls._key(user_id, portal, 'lock')

        def memory_release():
            _memory_locks.discard(lock_key)

        cls._redis_call(
            lambda r: r.delete(lock_key),
            memory_release,
        )

    @classmethod
    def check_hourly_cap(cls, user_id, portal: str) -> Optional[str]:
        count_key = cls._key(user_id, portal, 'count')
        mem_key = f'{user_id}:{portal}'

        def memory_check() -> Optional[str]:
            count, window_start = _memory_hourly_counts.get(mem_key, (0, datetime.utcnow()))
            if datetime.utcnow() - window_start >= timedelta(hours=1):
                return None
            if count >= cls.HOURLY_CAP:
                return f'Hourly scrape cap ({cls.HOURLY_CAP}) reached for {portal}'
            last = _memory_last_run.get(mem_key)
            if last and datetime.utcnow() - last < timedelta(minutes=3):
                return f'Please wait before scraping {portal} again'
            return None

        def redis_check(r) -> Optional[str]:
            count = int(r.get(count_key) or 0)
            if count >= cls.HOURLY_CAP:
                return f'Hourly scrape cap ({cls.HOURLY_CAP}) reached for {portal}'
            return None

        return cls._redis_call(redis_check, memory_check)

    @classmethod
    def record_run(cls, user_id, portal: str):
        count_key = cls._key(user_id, portal, 'count')
        mem_key = f'{user_id}:{portal}'

        def memory_record():
            count, window_start = _memory_hourly_counts.get(mem_key, (0, datetime.utcnow()))
            if datetime.utcnow() - window_start >= timedelta(hours=1):
                count, window_start = 0, datetime.utcnow()
            _memory_hourly_counts[mem_key] = (count + 1, window_start)
            _memory_last_run[mem_key] = datetime.utcnow()

        def redis_record(r):
            pipe = r.pipeline()
            pipe.incr(count_key)
            pipe.expire(count_key, 3600)
            pipe.execute()

        cls._redis_call(redis_record, memory_record)

    @classmethod
    def random_delay(cls):
        delay_ms = random.randint(cls.DELAY_MIN_MS, cls.DELAY_MAX_MS)
        time.sleep(delay_ms / 1000.0)


scrape_rate_limiter = ScrapeRateLimiter()
