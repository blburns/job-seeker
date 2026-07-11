"""Tests for scheduled discovery Celery tasks and beat config."""

from datetime import datetime, timedelta
from unittest.mock import patch

from app.extensions.celery_config import celery_config
from app.extensions.core import db
from app.models.jobs import JobSearchProfile
from app.tasks.job_tasks import run_all_active_discoveries


def test_beat_schedule_points_at_run_all_active_discoveries():
    entry = celery_config['beat_schedule']['run-active-job-discoveries']
    assert entry['task'] == 'app.tasks.job_tasks.run_all_active_discoveries'
    assert entry['schedule'] == 21600.0


def test_run_all_active_discoveries_skips_recent_and_inactive(app, test_user):
    with app.app_context():
        active_due = JobSearchProfile(
            user_id=test_user.id,
            name='Due',
            titles=['Engineer'],
            locations=[],
            sources=['remotive'],
            is_active=True,
            schedule_hours=6,
            last_run_at=None,
        )
        active_recent = JobSearchProfile(
            user_id=test_user.id,
            name='Recent',
            titles=['Engineer'],
            locations=[],
            sources=['remotive'],
            is_active=True,
            schedule_hours=6,
            last_run_at=datetime.utcnow() - timedelta(hours=1),
        )
        inactive = JobSearchProfile(
            user_id=test_user.id,
            name='Inactive',
            titles=['Engineer'],
            locations=[],
            sources=['remotive'],
            is_active=False,
            schedule_hours=6,
            last_run_at=None,
        )
        db.session.add_all([active_due, active_recent, inactive])
        db.session.commit()
        due_id = active_due.id

        with patch(
            'app.services.discovery_orchestrator.discovery_orchestrator.run_discovery'
        ) as mock_run:
            result = run_all_active_discoveries()

        assert result == {'success': True, 'profiles_run': 1}
        mock_run.assert_called_once_with(due_id, test_user.id)


def test_run_all_active_discoveries_runs_stale_profile(app, test_user):
    with app.app_context():
        stale = JobSearchProfile(
            user_id=test_user.id,
            name='Stale',
            titles=['Engineer'],
            locations=[],
            sources=['remotive'],
            is_active=True,
            schedule_hours=6,
            last_run_at=datetime.utcnow() - timedelta(hours=7),
        )
        db.session.add(stale)
        db.session.commit()
        stale_id = stale.id

        with patch(
            'app.services.discovery_orchestrator.discovery_orchestrator.run_discovery'
        ) as mock_run:
            result = run_all_active_discoveries()

        assert result['profiles_run'] == 1
        mock_run.assert_called_once_with(stale_id, test_user.id)
