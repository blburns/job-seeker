"""
Discovery orchestration — run connectors, deduplicate, score, and stage jobs.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.extensions.core import db
from app.models.jobs import (
    CompanyBlocklist,
    DiscoveredJob,
    DiscoveredJobStatus,
    DiscoveryRun,
    DiscoveryRunStatus,
    JobPosting,
    JobSearchProfile,
    JobSource,
    MasterProfile,
)
from app.services.discovery.base import DiscoverySearchError
from app.services.discovery import get_connectors
from app.services.job_discovery_service import job_discovery_service
from app.services.keyword_service import keyword_service

logger = logging.getLogger(__name__)


class DiscoveryOrchestrator:
    """Coordinate multi-source job discovery for a user."""

    @classmethod
    def profile_to_search_dict(cls, profile: JobSearchProfile) -> Dict[str, Any]:
        return {
            'titles': profile.titles or [],
            'locations': profile.locations or [],
            'remote_preference': profile.remote_preference,
            'seniority_levels': profile.seniority_levels or [],
            'min_fit_score': profile.min_fit_score or 0,
            'keywords_include': profile.keywords_include or [],
            'keywords_exclude': profile.keywords_exclude or [],
            'greenhouse_boards': profile.greenhouse_boards or [],
            'lever_boards': profile.lever_boards or [],
            'rss_feeds': profile.rss_feeds or [],
            'indeed_max_age_days': getattr(profile, 'indeed_max_age_days', None) or 7,
            'indeed_radius_miles': getattr(profile, 'indeed_radius_miles', None) or 0,
        }

    @classmethod
    def is_blocked(cls, user_id, company: str, url: str = '') -> bool:
        blocklist = CompanyBlocklist.query.filter_by(user_id=user_id).all()
        company_lower = (company or '').lower()
        url_lower = (url or '').lower()
        for entry in blocklist:
            if entry.company_name and entry.company_name.lower() in company_lower:
                return True
            if entry.url_pattern and entry.url_pattern.lower() in url_lower:
                return True
        return False

    @classmethod
    def is_duplicate(cls, user_id, url: str, source: str, source_id: str) -> bool:
        if url:
            exists = JobPosting.query.filter_by(
                user_id=user_id, url=url, is_deleted=False
            ).with_entities(JobPosting.id).first()
            if exists:
                return True
        if source_id:
            exists = DiscoveredJob.query.filter(
                DiscoveredJob.user_id == user_id,
                DiscoveredJob.source == source,
                DiscoveredJob.source_id == source_id,
                DiscoveredJob.status.in_([
                    DiscoveredJobStatus.NEW.value,
                    DiscoveredJobStatus.ACCEPTED.value,
                ]),
            ).with_entities(DiscoveredJob.id).first()
            if exists:
                return True
            exists = JobPosting.query.filter_by(
                user_id=user_id, source=source, source_id=source_id, is_deleted=False
            ).with_entities(JobPosting.id).first()
            if exists:
                return True
        return False

    @classmethod
    def calculate_fit(
        cls,
        description: str,
        user_id,
        title: str = '',
        company: str = '',
        profile_titles: Optional[List[str]] = None,
    ) -> int:
        row = MasterProfile.query.filter_by(
            user_id=user_id, is_active=True, is_deleted=False
        ).with_entities(MasterProfile.profile_data).first()
        if not row or not row[0]:
            return 0

        combined = ' '.join(part for part in (title, company, description) if part).strip()
        keywords = keyword_service.extract_keywords(combined or description or title or '')
        fit = job_discovery_service.calculate_fit_score(keywords, row[0])

        if fit == 0 and title and profile_titles:
            title_lower = title.lower()
            for profile_title in profile_titles:
                profile_title = (profile_title or '').lower().strip()
                if not profile_title:
                    continue
                if profile_title in title_lower or title_lower in profile_title:
                    fit = max(fit, 55)
                    break
                overlap = sum(
                    1 for word in profile_title.split()
                    if len(word) > 3 and word in title_lower
                )
                if overlap >= 2:
                    fit = max(fit, 50)
                    break
        return fit

    @classmethod
    def run_discovery(cls, profile_id, user_id, limit: int = 50) -> DiscoveryRun:
        profile = JobSearchProfile.query.filter_by(
            id=profile_id, user_id=user_id, is_deleted=False
        ).first_or_404()
        search_data = cls.profile_to_search_dict(profile)
        sources = profile.sources or ['adzuna', 'remotive']
        profile_titles = profile.titles or []
        last_run = None

        for connector in get_connectors(sources):
            run = DiscoveryRun(
                user_id=user_id,
                search_profile_id=profile.id,
                source=connector.source_name,
                status=DiscoveryRunStatus.RUNNING.value,
            )
            db.session.add(run)
            db.session.flush()
            jobs_new = 0

            try:
                dtos = connector.search(search_data, limit=limit, user_id=user_id)
                for dto in dtos:
                    if cls.is_blocked(user_id, dto.company, dto.url):
                        continue
                    fit = cls.calculate_fit(
                        dto.description, user_id, dto.title, dto.company, profile_titles,
                    )
                    if cls.is_duplicate(user_id, dto.url, dto.source, dto.source_id):
                        db.session.add(DiscoveredJob(
                            user_id=user_id,
                            search_profile_id=profile.id,
                            discovery_run_id=run.id,
                            title=dto.title,
                            company=dto.company,
                            description=dto.description,
                            location=dto.location,
                            url=dto.url,
                            source=dto.source,
                            source_id=dto.source_id,
                            fit_score=fit,
                            status=DiscoveredJobStatus.DUPLICATE.value,
                            raw_data=dto.raw_data,
                        ))
                        continue

                    exclude = [k.lower() for k in (profile.keywords_exclude or [])]
                    text = f"{dto.title} {dto.description}".lower()
                    if exclude and any(k in text for k in exclude):
                        continue

                    discovered = DiscoveredJob(
                        user_id=user_id,
                        search_profile_id=profile.id,
                        discovery_run_id=run.id,
                        title=dto.title,
                        company=dto.company,
                        description=dto.description,
                        location=dto.location,
                        url=dto.url,
                        source=dto.source,
                        source_id=dto.source_id,
                        fit_score=fit,
                        status=DiscoveredJobStatus.NEW.value,
                        raw_data=dto.raw_data,
                    )
                    db.session.add(discovered)
                    jobs_new += 1

                run.status = DiscoveryRunStatus.COMPLETED.value
                run.jobs_found = len(dtos)
                run.jobs_new = jobs_new
                run.completed_at = datetime.utcnow()
            except DiscoverySearchError as exc:
                logger.warning('Discovery search failed for %s: %s', connector.source_name, exc)
                run.status = DiscoveryRunStatus.FAILED.value
                run.error_message = str(exc)
                run.completed_at = datetime.utcnow()
            except Exception as exc:
                logger.exception('Discovery run failed for %s', connector.source_name)
                run.status = DiscoveryRunStatus.FAILED.value
                run.error_message = str(exc)
                run.completed_at = datetime.utcnow()

            last_run = run

        profile.last_run_at = datetime.utcnow()
        db.session.commit()
        return last_run

    @classmethod
    def accept_discovered_job(cls, discovered_id, user_id, create_application: bool = True):
        from app.models.jobs import Application, ApplicationStage

        discovered = DiscoveredJob.query.filter_by(
            id=discovered_id, user_id=user_id
        ).first_or_404()
        if discovered.status == DiscoveredJobStatus.ACCEPTED.value and discovered.job_posting_id:
            return discovered.job_posting

        keywords = keyword_service.extract_keywords(discovered.description or '')
        source_map = {
            'greenhouse': JobSource.GREENHOUSE.value,
            'lever': JobSource.LEVER.value,
            'adzuna': JobSource.ADZUNA.value,
            'remotive': JobSource.REMOTIVE.value,
            'rss': JobSource.RSS.value,
            'linkedin': JobSource.LINKEDIN.value,
            'indeed': JobSource.INDEED.value,
        }
        posting = JobPosting(
            user_id=user_id,
            title=discovered.title,
            company=discovered.company,
            description=discovered.description,
            location=discovered.location,
            url=discovered.url,
            source=source_map.get(discovered.source, JobSource.API.value),
            source_id=discovered.source_id,
            extracted_keywords=keywords,
            fit_score=discovered.fit_score,
        )
        db.session.add(posting)
        db.session.flush()

        discovered.status = DiscoveredJobStatus.ACCEPTED.value
        discovered.job_posting_id = posting.id

        if create_application:
            existing = Application.query.filter_by(
                user_id=user_id, job_posting_id=posting.id, is_deleted=False
            ).first()
            if not existing:
                app_record = Application(
                    user_id=user_id,
                    job_posting_id=posting.id,
                    stage=ApplicationStage.SAVED.value,
                    portal_url=posting.url,
                )
                db.session.add(app_record)
                db.session.flush()
                from app.services.activity_service import activity_service
                activity_service.log(
                    app_record.id, user_id, 'discovery',
                    subject='Job accepted from discovery inbox',
                )

        db.session.commit()
        return posting

    @classmethod
    def skip_discovered_job(cls, discovered_id, user_id):
        discovered = DiscoveredJob.query.filter_by(id=discovered_id, user_id=user_id).first_or_404()
        discovered.status = DiscoveredJobStatus.SKIPPED.value
        db.session.commit()
        return discovered


discovery_orchestrator = DiscoveryOrchestrator()
