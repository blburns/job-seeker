"""API tests for company blocklist CRUD."""

from app.extensions.core import db
from app.models.jobs import CompanyBlocklist


def test_blocklist_api_crud(app, auth_client, test_user):
    create = auth_client.post(
        '/api/v1/jobs/blocklist',
        json={'company_name': 'NoHire Inc', 'reason': 'Not a fit'},
    )
    assert create.status_code == 201
    entry_id = create.get_json()['id']

    listed = auth_client.get('/api/v1/jobs/blocklist')
    assert listed.status_code == 200
    assert any(e['id'] == entry_id for e in listed.get_json()['data'])

    patched = auth_client.patch(
        f'/api/v1/jobs/blocklist/{entry_id}',
        json={'url_pattern': 'example.com/nohire', 'company_name': 'NoHire Inc'},
    )
    assert patched.status_code == 200
    assert patched.get_json()['url_pattern'] == 'example.com/nohire'

    deleted = auth_client.delete(f'/api/v1/jobs/blocklist/{entry_id}')
    assert deleted.status_code == 200
    with app.app_context():
        assert CompanyBlocklist.query.filter_by(id=entry_id).first() is None


def test_blocklist_api_requires_company_or_url(auth_client):
    resp = auth_client.post('/api/v1/jobs/blocklist', json={'reason': 'oops'})
    assert resp.status_code == 400


def test_blocklist_html_list(auth_client):
    resp = auth_client.get('/jobs/blocklist')
    assert resp.status_code == 200
    assert b'Company Blocklist' in resp.data
