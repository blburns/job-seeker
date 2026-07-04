"""Discovery connector protocol and DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class DiscoverySearchError(Exception):
    """Raised when a connector cannot complete discovery (auth, rate limit, etc.)."""


@dataclass
class DiscoveredJobDTO:
    title: str
    company: str
    description: str = ''
    url: str = ''
    source: str = 'api'
    source_id: str = ''
    location: str = ''
    seniority: str = ''
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


class DiscoveryConnector(Protocol):
    source_name: str

    def search(
        self,
        profile_data: Dict[str, Any],
        limit: int = 50,
        user_id=None,
    ) -> List[DiscoveredJobDTO]:
        ...
