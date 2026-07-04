"""Tests for credential vault storage_state normalization."""

from app.services.credential_vault_service import credential_vault_service


def test_normalize_raw_storage_state():
    raw = {'cookies': [{'name': 'li_at', 'value': 'x'}], 'origins': []}
    normalized = credential_vault_service.normalize_credential_data(raw)
    assert 'storage_state' in normalized
    assert normalized['storage_state']['cookies'][0]['name'] == 'li_at'
    assert 'connected_at' in normalized


def test_normalize_wrapped_storage_state():
    wrapped = {'storage_state': {'cookies': [], 'origins': []}}
    normalized = credential_vault_service.normalize_credential_data(wrapped)
    assert normalized['storage_state']['cookies'] == []


def test_validate_linkedin_requires_li_at():
    try:
        credential_vault_service.validate_portal_data('linkedin', {
            'storage_state': {'cookies': [{'name': 'other', 'value': 'x'}], 'origins': []},
        })
        assert False, 'expected ValueError'
    except ValueError as exc:
        assert 'li_at' in str(exc)


def test_ephemeral_key_stable_within_process(app, db_session):
    from app.models.auth import User

    user = User(email='key@test.com', username='keyuser', password_hash='hash')
    db_session.add(user)
    db_session.commit()

    data = {
        'storage_state': {
            'cookies': [{'name': 'li_at', 'value': 'session-token'}],
            'origins': [],
        },
    }
    credential_vault_service.store(user.id, 'linkedin', data)
    loaded, error = credential_vault_service.retrieve_with_status(user.id, 'linkedin')
    assert error is None
    assert loaded['storage_state']['cookies'][0]['name'] == 'li_at'


def test_store_replaces_and_delete(app, db_session):
    import uuid
    from app.models.auth import User
    from app.models.jobs import PortalCredential

    user = User(email='cred@test.com', username='creduser', password_hash='hash')
    db_session.add(user)
    db_session.commit()

    data = {'storage_state': {'cookies': [{'name': 'li_at', 'value': '1'}], 'origins': []}}
    first = credential_vault_service.store(user.id, 'linkedin', data, label='first')
    second = credential_vault_service.store(user.id, 'linkedin', data, label='second')

    first = PortalCredential.query.get(first.id)
    assert first.is_deleted is True
    assert second.is_active is True
    assert credential_vault_service.has_active(user.id, 'linkedin') is True

    assert credential_vault_service.delete(user.id, second.id) is True
    assert credential_vault_service.has_active(user.id, 'linkedin') is False

    credential_vault_service.store(user.id, 'linkedin', data, label='third')
    removed = credential_vault_service.delete_for_portal(user.id, 'linkedin')
    assert removed == 1
    assert credential_vault_service.list_credentials(user.id) == []
