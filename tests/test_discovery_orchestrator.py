"""Tests for discovery orchestrator dedup logic."""

import uuid

import pytest

from app.extensions.core import db
from app.models.jobs import DiscoveredJob, DiscoveredJobStatus, JobPosting, JobSource
from app.services.discovery_orchestrator import DiscoveryOrchestrator


@pytest.fixture
def user_id():
    return uuid.uuid4()


def test_is_duplicate_by_url(app, user_id):
    with app.app_context():
        posting = JobPosting(
            user_id=user_id,
            title='Engineer',
            company='Acme',
            url='https://example.com/job/1',
            source=JobSource.MANUAL.value,
        )
        db.session.add(posting)
        db.session.commit()
        assert DiscoveryOrchestrator.is_duplicate(
            user_id, 'https://example.com/job/1', 'manual', ''
        ) is True
        assert DiscoveryOrchestrator.is_duplicate(
            user_id, 'https://example.com/job/2', 'manual', ''
        ) is False


def test_is_duplicate_by_source_id(app, user_id):
    with app.app_context():
        discovered = DiscoveredJob(
            user_id=user_id,
            title='Engineer',
            company='Acme',
            source='greenhouse',
            source_id='gh-123',
            status=DiscoveredJobStatus.NEW.value,
        )
        db.session.add(discovered)
        db.session.commit()
        assert DiscoveryOrchestrator.is_duplicate(
            user_id, '', 'greenhouse', 'gh-123'
        ) is True


def test_is_duplicate_ignores_skipped_and_duplicate_status(app, user_id):
    with app.app_context():
        db.session.add(DiscoveredJob(
            user_id=user_id,
            title='Engineer',
            company='Acme',
            source='indeed',
            source_id='jk-999',
            status=DiscoveredJobStatus.DUPLICATE.value,
        ))
        db.session.commit()
        assert DiscoveryOrchestrator.is_duplicate(
            user_id, 'https://indeed.com/viewjob?jk=jk-999', 'indeed', 'jk-999'
        ) is False


def test_is_blocked_company(app, user_id):
    from app.models.jobs import CompanyBlocklist
    with app.app_context():
        db.session.add(CompanyBlocklist(
            user_id=user_id,
            company_name='BadCorp',
        ))
        db.session.commit()
        assert DiscoveryOrchestrator.is_blocked(user_id, 'BadCorp Inc', '') is True
        assert DiscoveryOrchestrator.is_blocked(user_id, 'GoodCo', '') is False


def test_is_blocked_url_pattern(app, user_id):
    from app.models.jobs import CompanyBlocklist
    with app.app_context():
        db.session.add(CompanyBlocklist(
            user_id=user_id,
            url_pattern='boards.greenhouse.io/badco',
        ))
        db.session.commit()
        assert DiscoveryOrchestrator.is_blocked(
            user_id, 'Anything', 'https://boards.greenhouse.io/badco/jobs/1'
        ) is True
        assert DiscoveryOrchestrator.is_blocked(
            user_id, 'Anything', 'https://boards.greenhouse.io/goodco/jobs/1'
        ) is False


def test_block_discovered_company(app, user_id):
    from app.models.jobs import CompanyBlocklist
    with app.app_context():
        discovered = DiscoveredJob(
            user_id=user_id,
            title='Engineer',
            company='SpamCorp',
            source='remotive',
            source_id='sc-1',
            status=DiscoveredJobStatus.NEW.value,
        )
        db.session.add(discovered)
        db.session.commit()
        result = DiscoveryOrchestrator.block_discovered_company(discovered.id, user_id)
        assert result.status == DiscoveredJobStatus.SKIPPED.value
        assert CompanyBlocklist.query.filter_by(
            user_id=user_id, company_name='SpamCorp'
        ).count() == 1
