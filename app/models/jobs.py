"""
Jobs Schema Models
Job seeker automation: master profiles, job postings, applications, resume versions
"""

import os
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, JSON
from app.models.base import ID_TYPE
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.extensions.core import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


def _jobs_schema():
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        return 'jobs'
    return None


def _table_args():
    schema = _jobs_schema()
    return {'schema': schema} if schema else {}


def _fk(table):
    schema = _jobs_schema()
    prefix = f'{schema}.' if schema else ''
    return f'{prefix}{table}'


def _json_type():
    return JSONB if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql' else JSON


def _numeric_col(precision, scale, **kwargs):
    """SQLite lacks native Decimal; use float there to avoid SAWarnings."""
    asdecimal = os.environ.get('DB_TYPE', 'sqlite') == 'postgresql'
    return Numeric(precision, scale, asdecimal=asdecimal, **kwargs)


def _user_fk():
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        return 'auth.users.id'
    return 'users.id'


class ApplicationStage(PyEnum):
    SAVED = 'saved'
    TAILORING = 'tailoring'
    READY_TO_APPLY = 'ready_to_apply'
    APPLIED = 'applied'
    PHONE_SCREEN = 'phone_screen'
    INTERVIEW = 'interview'
    OFFER = 'offer'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'


class ResumeVersionStatus(PyEnum):
    DRAFT = 'draft'
    PENDING_APPROVAL = 'pending_approval'
    APPROVED = 'approved'
    ARCHIVED = 'archived'


class JobSource(PyEnum):
    MANUAL = 'manual'
    URL = 'url'
    RSS = 'rss'
    API = 'api'
    GREENHOUSE = 'greenhouse'
    LEVER = 'lever'
    ASHBY = 'ashby'
    ADZUNA = 'adzuna'
    REMOTIVE = 'remotive'
    LINKEDIN = 'linkedin'
    INDEED = 'indeed'


class DiscoveredJobStatus(PyEnum):
    NEW = 'new'
    ACCEPTED = 'accepted'
    SKIPPED = 'skipped'
    DUPLICATE = 'duplicate'


class ApplyBatchStatus(PyEnum):
    DRAFT = 'draft'
    APPROVED = 'approved'
    RUNNING = 'running'
    COMPLETED = 'completed'
    PARTIAL_FAILURE = 'partial_failure'


class DiscoveryRunStatus(PyEnum):
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class SubmissionStatus(PyEnum):
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    NEEDS_MANUAL = 'needs_manual'
    FAILED = 'failed'


class PortalType(PyEnum):
    GREENHOUSE = 'greenhouse'
    LEVER = 'lever'
    ASHBY = 'ashby'
    LINKEDIN = 'linkedin'
    INDEED = 'indeed'
    GENERIC = 'generic'


class MasterProfile(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Canonical structured resume data per user."""
    __tablename__ = 'master_profiles'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    headline = Column(String(255), nullable=True)
    profile_data = Column(_json_type(), nullable=False, default=dict)
    source_filename = Column(String(255), nullable=True)
    source_type = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    parse_confidence = Column(_numeric_col(5, 2), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='master_profiles')
    resume_versions = relationship('ResumeVersion', back_populates='master_profile')

    @property
    def contact(self):
        return (self.profile_data or {}).get('contact', {})

    @property
    def full_name(self):
        return self.contact.get('name', 'Unknown')


class JobPosting(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Job posting from manual paste, URL, or API."""
    __tablename__ = 'job_postings'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    remote_type = Column(String(50), nullable=True)
    salary_min = Column(_numeric_col(12, 2), nullable=True)
    salary_max = Column(_numeric_col(12, 2), nullable=True)
    salary_currency = Column(String(3), default='USD', nullable=False)
    url = Column(String(1024), nullable=True)
    source = Column(String(50), default=JobSource.MANUAL.value, nullable=False)
    source_id = Column(String(255), nullable=True)
    seniority = Column(String(50), nullable=True)
    extracted_keywords = Column(_json_type(), nullable=True)
    fit_score = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='job_postings')
    applications = relationship('Application', back_populates='job_posting')
    keyword_analyses = relationship('KeywordAnalysis', back_populates='job_posting')

    @property
    def discovery_search_profiles(self):
        """Search profiles that discovered this posting (via discovery inbox)."""
        profiles = []
        seen = set()
        for discovered in self.discovered_jobs or []:
            profile = discovered.search_profile
            if not profile or profile.is_deleted or profile.id in seen:
                continue
            seen.add(profile.id)
            profiles.append(profile)
        return profiles


class ResumeVersion(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Tailored resume version for a specific job."""
    __tablename__ = 'resume_versions'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    master_profile_id = Column(ID_TYPE, ForeignKey(_fk('master_profiles.id')), nullable=False, index=True)
    job_posting_id = Column(ID_TYPE, ForeignKey(_fk('job_postings.id')), nullable=True, index=True)
    version_number = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default=ResumeVersionStatus.DRAFT.value, nullable=False, index=True)
    tailored_data = Column(_json_type(), nullable=False, default=dict)
    diff_log = Column(_json_type(), nullable=True)
    ats_score = Column(_numeric_col(5, 2), nullable=True)
    keyword_coverage = Column(_numeric_col(5, 2), nullable=True)
    export_filename = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=True)

    master_profile = relationship('MasterProfile', back_populates='resume_versions')
    job_posting = relationship('JobPosting', backref='resume_versions')
    user = relationship('User', foreign_keys=[user_id], backref='resume_versions')
    applications = relationship('Application', back_populates='resume_version')


class Application(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Job application tracking record."""
    __tablename__ = 'applications'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    job_posting_id = Column(ID_TYPE, ForeignKey(_fk('job_postings.id')), nullable=False, index=True)
    resume_version_id = Column(ID_TYPE, ForeignKey(_fk('resume_versions.id')), nullable=True, index=True)
    stage = Column(String(50), default=ApplicationStage.SAVED.value, nullable=False, index=True)
    applied_at = Column(DateTime, nullable=True)
    response_at = Column(DateTime, nullable=True)
    recruiter_name = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    portal_url = Column(String(1024), nullable=True)
    keyword_coverage_at_apply = Column(_numeric_col(5, 2), nullable=True)
    notes = Column(Text, nullable=True)
    submission_status = Column(String(50), nullable=True)
    submission_proof = Column(String(1024), nullable=True)
    submission_error = Column(Text, nullable=True)
    apply_batch_id = Column(ID_TYPE, ForeignKey(_fk('apply_batches.id')), nullable=True, index=True)
    follow_up_at = Column(DateTime, nullable=True)
    custom_fields = Column(_json_type(), nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='applications')
    job_posting = relationship('JobPosting', back_populates='applications')
    resume_version = relationship('ResumeVersion', back_populates='applications')
    activities = relationship('ApplicationActivity', back_populates='application', order_by='ApplicationActivity.created_at.desc()')
    apply_drafts = relationship('ApplyDraft', back_populates='application')


class ApplicationActivity(BaseModel, TimestampMixin):
    """Activity timeline for an application."""
    __tablename__ = 'application_activities'
    __table_args__ = _table_args()

    application_id = Column(ID_TYPE, ForeignKey(_fk('applications.id')), nullable=False, index=True)
    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False)
    activity_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    activity_metadata = Column(_json_type(), nullable=True)

    application = relationship('Application', back_populates='activities')
    user = relationship('User', foreign_keys=[user_id])


class KeywordAnalysis(BaseModel, TimestampMixin):
    """Keyword gap analysis between JD and master profile."""
    __tablename__ = 'keyword_analyses'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    job_posting_id = Column(ID_TYPE, ForeignKey(_fk('job_postings.id')), nullable=False, index=True)
    master_profile_id = Column(ID_TYPE, ForeignKey(_fk('master_profiles.id')), nullable=False, index=True)
    jd_keywords = Column(_json_type(), nullable=False, default=list)
    matched_keywords = Column(_json_type(), nullable=False, default=list)
    missing_keywords = Column(_json_type(), nullable=False, default=list)
    synonym_matches = Column(_json_type(), nullable=True)
    coverage_score = Column(_numeric_col(5, 2), nullable=False, default=0)
    analysis_metadata = Column(_json_type(), nullable=True)

    job_posting = relationship('JobPosting', back_populates='keyword_analyses')
    master_profile = relationship('MasterProfile')
    user = relationship('User', foreign_keys=[user_id])


class ApplyDraft(BaseModel, TimestampMixin):
    """Pre-filled application form awaiting user approval."""
    __tablename__ = 'apply_drafts'
    __table_args__ = _table_args()

    application_id = Column(ID_TYPE, ForeignKey(_fk('applications.id')), nullable=False, index=True)
    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False)
    form_fields = Column(_json_type(), nullable=False, default=dict)
    cover_letter = Column(Text, nullable=True)
    status = Column(String(50), default='draft', nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    application = relationship('Application', back_populates='apply_drafts')
    user = relationship('User', foreign_keys=[user_id])


class JobSearchProfile(BaseModel, TimestampMixin, SoftDeleteMixin):
    """User job search criteria for automated discovery."""
    __tablename__ = 'job_search_profiles'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    titles = Column(_json_type(), nullable=False, default=list)
    locations = Column(_json_type(), nullable=False, default=list)
    remote_preference = Column(String(50), default='any', nullable=False)
    seniority_levels = Column(_json_type(), nullable=True)
    min_fit_score = Column(Integer, default=50, nullable=False)
    salary_floor = Column(_numeric_col(12, 2), nullable=True)
    keywords_include = Column(_json_type(), nullable=True)
    keywords_exclude = Column(_json_type(), nullable=True)
    sources = Column(_json_type(), nullable=False, default=list)
    greenhouse_boards = Column(_json_type(), nullable=True)
    lever_boards = Column(_json_type(), nullable=True)
    rss_feeds = Column(_json_type(), nullable=True)
    indeed_max_age_days = Column(Integer, default=7, nullable=True)
    indeed_radius_miles = Column(Integer, default=0, nullable=True)
    schedule_hours = Column(Integer, default=6, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='job_search_profiles')
    discovery_runs = relationship('DiscoveryRun', back_populates='search_profile')


class CompanyBlocklist(BaseModel, TimestampMixin):
    """Companies or URL patterns to skip during discovery."""
    __tablename__ = 'company_blocklists'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    url_pattern = Column(String(512), nullable=True)
    reason = Column(String(255), nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='company_blocklists')


class DiscoveryRun(BaseModel, TimestampMixin):
    """Audit log for a discovery execution."""
    __tablename__ = 'discovery_runs'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    search_profile_id = Column(ID_TYPE, ForeignKey(_fk('job_search_profiles.id')), nullable=True, index=True)
    source = Column(String(50), nullable=False)
    status = Column(String(50), default=DiscoveryRunStatus.RUNNING.value, nullable=False)
    jobs_found = Column(Integer, default=0, nullable=False)
    jobs_new = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    run_metadata = Column(_json_type(), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    search_profile = relationship('JobSearchProfile', back_populates='discovery_runs')
    user = relationship('User', foreign_keys=[user_id])


class DiscoveredJob(BaseModel, TimestampMixin):
    """Staging record before promotion to JobPosting."""
    __tablename__ = 'discovered_jobs'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    search_profile_id = Column(ID_TYPE, ForeignKey(_fk('job_search_profiles.id')), nullable=True, index=True)
    discovery_run_id = Column(ID_TYPE, ForeignKey(_fk('discovery_runs.id')), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    source = Column(String(50), nullable=False)
    source_id = Column(String(255), nullable=True)
    fit_score = Column(Integer, nullable=True)
    status = Column(String(50), default=DiscoveredJobStatus.NEW.value, nullable=False, index=True)
    job_posting_id = Column(ID_TYPE, ForeignKey(_fk('job_postings.id')), nullable=True)
    raw_data = Column(_json_type(), nullable=True)

    user = relationship('User', foreign_keys=[user_id])
    job_posting = relationship('JobPosting', backref='discovered_jobs')
    search_profile = relationship('JobSearchProfile', foreign_keys=[search_profile_id])
    discovery_run = relationship('DiscoveryRun', foreign_keys=[discovery_run_id])


class ApplyBatch(BaseModel, TimestampMixin):
    """Batch of applications approved for automated submission."""
    __tablename__ = 'apply_batches'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    status = Column(String(50), default=ApplyBatchStatus.DRAFT.value, nullable=False, index=True)
    application_ids = Column(_json_type(), nullable=False, default=list)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    batch_metadata = Column(_json_type(), nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='apply_batches')
    items = relationship('ApplyBatchItem', back_populates='batch')


class ApplyBatchItem(BaseModel, TimestampMixin):
    """Per-application progress within an apply batch."""
    __tablename__ = 'apply_batch_items'
    __table_args__ = _table_args()

    batch_id = Column(ID_TYPE, ForeignKey(_fk('apply_batches.id')), nullable=False, index=True)
    application_id = Column(ID_TYPE, ForeignKey(_fk('applications.id')), nullable=False, index=True)
    status = Column(String(50), default='pending', nullable=False)
    submission_status = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    proof_path = Column(String(1024), nullable=True)

    batch = relationship('ApplyBatch', back_populates='items')
    application = relationship('Application', backref='batch_items')


class PortalCredential(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Encrypted portal session credentials for auto-apply."""
    __tablename__ = 'portal_credentials'
    __table_args__ = _table_args()

    user_id = Column(ID_TYPE, ForeignKey(_user_fk()), nullable=False, index=True)
    portal = Column(String(50), nullable=False, index=True)
    label = Column(String(255), nullable=True)
    encrypted_data = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='portal_credentials')
