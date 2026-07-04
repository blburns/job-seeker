"""RSS feed discovery connector."""

import logging
from typing import Any, Dict, List

from app.services.discovery.base import DiscoveredJobDTO
from app.services.job_discovery_service import job_discovery_service

logger = logging.getLogger(__name__)


class RssConnector:
    source_name = 'rss'

    def search(self, profile_data: Dict[str, Any], limit: int = 50, user_id=None) -> List[DiscoveredJobDTO]:
        feeds = profile_data.get('rss_feeds') or []
        titles = [t.lower() for t in (profile_data.get('titles') or [])]
        results: List[DiscoveredJobDTO] = []

        for feed_url in feeds:
            try:
                items = job_discovery_service.search_rss_feed(feed_url, limit=limit)
            except Exception as exc:
                logger.warning('RSS fetch failed for %s: %s', feed_url, exc)
                continue
            for item in items:
                title = item.get('title', '')
                if titles and not any(t in title.lower() for t in titles):
                    continue
                results.append(DiscoveredJobDTO(
                    title=title,
                    company=item.get('company', '') or 'Unknown',
                    description=item.get('description', ''),
                    url=item.get('url', ''),
                    source=self.source_name,
                    source_id=item.get('url', ''),
                    raw_data=item,
                ))
                if len(results) >= limit:
                    return results
        return results
