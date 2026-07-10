"""Tests for apply batch retry and automation kill switch."""

from datetime import datetime
from unittest.mock import patch

import pytest

from app.models.jobs import (
    Application,
    ApplicationStage,
    ApplyBatch,
    ApplyBatchItem,
    ApplyBatchStatus,
    JobPosting,
    SubmissionStatus,
)
from app.services.apply_batch_service import apply_batch_service
from app.services.apply_submission_service import apply_submission_service


def _seed_batch(db_session, user, status=ApplyBatchStatus.PARTIAL_FAILURE.value):
    posting = JobPosting(
        user_id=user.id,
        title='Engineer',
        company='Acme',
        description='Python role',
        url='https://boards.greenhouse.io/acme/jobs/1',
        source='manual',
    )
    db_session.add(posting)
    db_session.flush()
    app = Application(
        user_id=user.id,
        job_posting_id=posting.id,
        stage=ApplicationStage.READY_TO_APPLY.value,
        submission_status=SubmissionStatus.NEEDS_MANUAL.value,
    )
    db_session.add(app)
    db_session.flush()
    batch = ApplyBatch(
        user_id=user.id,
        status=status,
        application_ids=[str(app.id)],
        completed_at=datetime.utcnow(),
    )
    db_session.add(batch)
    db_session.flush()
    item = ApplyBatchItem(
        batch_id=batch.id,
        application_id=app.id,
        status='needs_manual',
        error_message='needs review',
    )
    db_session.add(item)
    db_session.commit()
    return batch, app


def test_prepare_retry_resets_failed_items(app, db_session, test_user):
    with app.app_context():
        batch, _app = _seed_batch(db_session, test_user)
        updated = apply_batch_service.prepare_retry(test_user.id, batch.id)
        assert updated.status == ApplyBatchStatus.APPROVED.value
        item = ApplyBatchItem.query.filter_by(batch_id=batch.id).first()
        assert item.status == 'pending'
        assert item.error_message is None


def test_prepare_retry_rejects_draft(app, db_session, test_user):
    with app.app_context():
        batch, _app = _seed_batch(db_session, test_user, status=ApplyBatchStatus.DRAFT.value)
        with pytest.raises(ValueError, match='cannot be retried'):
            apply_batch_service.prepare_retry(test_user.id, batch.id)


def test_automation_kill_switch_blocks_batch(monkeypatch):
    monkeypatch.setenv('AUTOMATION_DISABLED', 'true')
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'true')
    reason = apply_submission_service.automation_blocked()
    assert 'kill switch' in reason.lower()


def test_automation_blocked_when_flag_off(monkeypatch):
    monkeypatch.setenv('AUTOMATION_DISABLED', 'false')
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'false')
    reason = apply_submission_service.automation_blocked()
    assert 'APPLY_AUTOMATION_ENABLED' in reason
