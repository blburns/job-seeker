"""
Models Package
Database models for job seeker automation app
"""

from .base import BaseModel, TimestampMixin, SoftDeleteMixin
from .auth import User, Role, Group, user_groups, user_roles, group_roles

try:
    from .jobs import (
        MasterProfile, JobPosting, ResumeVersion, Application,
        ApplicationActivity, KeywordAnalysis, ApplyDraft,
        ApplicationStage, ResumeVersionStatus, JobSource,
    )
    HAS_JOBS = True
except ImportError:
    HAS_JOBS = False

__all__ = [
    'BaseModel', 'TimestampMixin', 'SoftDeleteMixin',
    'User', 'Role', 'Group', 'user_groups', 'user_roles', 'group_roles',
]

if HAS_JOBS:
    __all__.extend([
        'MasterProfile', 'JobPosting', 'ResumeVersion', 'Application',
        'ApplicationActivity', 'KeywordAnalysis', 'ApplyDraft',
        'ApplicationStage', 'ResumeVersionStatus', 'JobSource',
    ])
