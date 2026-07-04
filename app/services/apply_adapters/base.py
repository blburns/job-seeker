"""Apply adapter types and result DTOs."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol


@dataclass
class ApplyContext:
    application_id: str
    job_url: str
    job_title: str
    company: str
    resume_path: str
    form_fields: Dict[str, Any]
    user_id: str
    portal_credentials: Optional[Dict[str, Any]] = None


@dataclass
class ApplyResult:
    success: bool
    status: str  # submitted, needs_manual, failed
    message: str = ''
    proof_path: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)


class ApplyAdapter(Protocol):
    portal_name: str

    def can_handle(self, url: str) -> bool:
        ...

    def submit(self, context: ApplyContext) -> ApplyResult:
        ...
