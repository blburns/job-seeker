"""Tests for portal session health helpers."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.scraping.scrape_result import ScrapeResult, ScrapeStatus
from app.services.scraping.session_health import SessionHealthService, session_health


def test_reauth_message_includes_portal_and_hint():
    msg = session_health.reauth_message('linkedin', ScrapeStatus.AUTH_REQUIRED, 'Login required')
    assert 'LinkedIn' in msg
    assert 'Portal Credentials' in msg
    assert 'Login required' in msg


def test_credential_health_label_states():
    assert session_health.credential_health_label(SimpleNamespace(is_active=False)) == 'inactive'
    assert session_health.credential_health_label(
        SimpleNamespace(is_active=True, expires_at=None)
    ) == 'untested'
    assert session_health.credential_health_label(
        SimpleNamespace(is_active=True, expires_at=datetime.utcnow() - timedelta(hours=1))
    ) == 'expired'
    assert session_health.credential_health_label(
        SimpleNamespace(is_active=True, expires_at=datetime.utcnow() + timedelta(days=3))
    ) == 'healthy'


def test_check_and_update_sets_expires_on_success(app, db_session, test_user):
    from app.models.jobs import PortalCredential
    from app.services.credential_vault_service import credential_vault_service

    with app.app_context():
        credential_vault_service.store(
            test_user.id,
            'linkedin',
            {
                'storage_state': {
                    'cookies': [{'name': 'li_at', 'value': 'tok'}],
                    'origins': [],
                }
            },
            label='test',
        )
        ok = ScrapeResult.success(message='Session is valid')
        with patch.object(SessionHealthService, 'check', return_value=ok):
            result = session_health.check_and_update_credential(test_user.id, 'linkedin')
        assert result.ok
        cred = PortalCredential.query.filter_by(
            user_id=test_user.id, portal='linkedin', is_active=True
        ).first()
        assert cred is not None
        assert cred.expires_at is not None
        assert cred.expires_at > datetime.utcnow()
        assert cred.last_used_at is not None


def test_check_and_update_marks_expired_on_auth_failure(app, db_session, test_user):
    from app.models.jobs import PortalCredential
    from app.services.credential_vault_service import credential_vault_service

    with app.app_context():
        credential_vault_service.store(
            test_user.id,
            'linkedin',
            {
                'storage_state': {
                    'cookies': [{'name': 'li_at', 'value': 'tok'}],
                    'origins': [],
                }
            },
            label='test',
        )
        fail = ScrapeResult.failure(ScrapeStatus.AUTH_REQUIRED, 'Login required')
        with patch.object(SessionHealthService, 'check', return_value=fail):
            result = session_health.check_and_update_credential(test_user.id, 'linkedin')
        assert not result.ok
        assert 'Portal Credentials' in result.message
        cred = PortalCredential.query.filter_by(
            user_id=test_user.id, portal='linkedin', is_active=True
        ).first()
        assert cred.expires_at is not None
        assert cred.expires_at <= datetime.utcnow()
