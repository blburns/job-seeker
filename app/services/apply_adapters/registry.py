"""Apply adapter registry."""

import logging
from typing import List, Optional

from app.services.apply_adapters.base import ApplyAdapter, ApplyContext, ApplyResult

logger = logging.getLogger(__name__)

_ADAPTERS: List[ApplyAdapter] = []


def register_adapter(adapter: ApplyAdapter):
    _ADAPTERS.append(adapter)


def get_adapter(url: str) -> Optional[ApplyAdapter]:
    for adapter in _ADAPTERS:
        if adapter.can_handle(url):
            return adapter
    return None


def submit_application(context: ApplyContext) -> ApplyResult:
    adapter = get_adapter(context.job_url)
    if not adapter:
        from app.services.apply_adapters.generic import GenericAdapter
        adapter = GenericAdapter()
    return adapter.submit(context)


def _load_adapters():
    from app.services.apply_adapters.generic import GenericAdapter
    from app.services.apply_adapters.greenhouse import GreenhouseAdapter
    from app.services.apply_adapters.indeed import IndeedAdapter
    from app.services.apply_adapters.lever import LeverAdapter
    from app.services.apply_adapters.linkedin import LinkedInAdapter
    for cls in (GreenhouseAdapter, LeverAdapter, LinkedInAdapter, IndeedAdapter, GenericAdapter):
        register_adapter(cls())


_load_adapters()
