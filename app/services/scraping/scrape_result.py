"""Typed outcomes for portal scraping operations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScrapeStatus(str, Enum):
    SUCCESS = 'success'
    AUTH_REQUIRED = 'auth_required'
    CAPTCHA = 'captcha'
    BLOCKED = 'blocked'
    RATE_LIMITED = 'rate_limited'
    DISABLED = 'disabled'
    PARSE_ERROR = 'parse_error'
    ERROR = 'error'


@dataclass
class ScrapeResult:
    status: ScrapeStatus
    message: str = ''
    html: str = ''
    url: str = ''
    proof_path: str = ''
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == ScrapeStatus.SUCCESS

    @classmethod
    def success(cls, html: str = '', url: str = '', jobs: Optional[List[Dict[str, Any]]] = None, **metadata):
        return cls(
            status=ScrapeStatus.SUCCESS,
            message='OK',
            html=html,
            url=url,
            jobs=jobs or [],
            metadata=metadata,
        )

    @classmethod
    def failure(cls, status: ScrapeStatus, message: str, proof_path: str = '', url: str = ''):
        return cls(status=status, message=message, proof_path=proof_path, url=url)
