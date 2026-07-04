"""Application activity timeline helpers."""

import logging
from typing import Any, Dict, Optional

from app.extensions.core import db
from app.models.jobs import ApplicationActivity

logger = logging.getLogger(__name__)


class ActivityService:
    @classmethod
    def log(
        cls,
        application_id,
        user_id,
        activity_type: str,
        subject: str = '',
        description: str = '',
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApplicationActivity:
        activity = ApplicationActivity(
            application_id=application_id,
            user_id=user_id,
            activity_type=activity_type,
            subject=subject,
            description=description,
            activity_metadata=metadata or {},
        )
        db.session.add(activity)
        return activity


activity_service = ActivityService()
