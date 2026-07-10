"""End-to-end smoke test for the manual job application workflow."""


def test_manual_workflow_upload_to_applied(auth_client, sample_master_profile):
    """upload → save profile → create posting → create app → tailor → approve → draft → mark applied"""
    # 1. Save master profile
    resp = auth_client.post('/api/v1/resume/profiles', json={
        'profile_data': sample_master_profile,
        'source_type': 'manual',
        'parse_confidence': 100,
    })
    assert resp.status_code == 201, resp.get_json()
    profile = resp.get_json()
    assert profile.get('is_active') is True

    # 2. Create job posting
    resp = auth_client.post('/api/v1/jobs/postings', json={
        'title': 'Senior Python Engineer',
        'company': 'Acme Corp',
        'description': (
            'We need a Python engineer with Flask, AWS, and PostgreSQL experience. '
            'Kubernetes and Docker preferred.'
        ),
        'location': 'Remote',
        'source': 'manual',
    })
    assert resp.status_code == 201, resp.get_json()
    posting = resp.get_json()
    posting_id = posting['id']

    # 3. Create application
    resp = auth_client.post('/api/v1/applications/', json={
        'job_posting_id': posting_id,
    })
    assert resp.status_code == 201, resp.get_json()
    application = resp.get_json()
    app_id = application['id']
    assert application['stage'] == 'saved'

    # 4. Tailor resume
    resp = auth_client.post(f'/api/v1/applications/{app_id}/tailor')
    assert resp.status_code == 200, resp.get_json()
    tailor_result = resp.get_json()
    assert 'version' in tailor_result
    assert tailor_result['version']['status'] == 'pending_approval'

    # 5. Approve resume
    resp = auth_client.post(f'/api/v1/applications/{app_id}/approve')
    assert resp.status_code == 200, resp.get_json()
    approved = resp.get_json()
    assert approved['application']['stage'] == 'ready_to_apply'
    assert approved['version']['status'] == 'approved'

    # 6. Create apply draft
    resp = auth_client.post(f'/api/v1/apply/drafts/{app_id}')
    assert resp.status_code == 201, resp.get_json()
    draft = resp.get_json()
    draft_id = draft['id']
    assert draft.get('cover_letter')

    # 7. Approve draft
    resp = auth_client.post(f'/api/v1/apply/drafts/{draft_id}/approve', json={
        'form_fields': draft.get('form_fields') or {},
    })
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()['status'] == 'approved'

    # 8. Mark applied
    resp = auth_client.post(f'/api/v1/apply/submit/{app_id}')
    assert resp.status_code == 200, resp.get_json()
    applied = resp.get_json()
    assert applied['stage'] == 'applied'
    assert applied.get('applied_at')


def test_soft_delete_posting_and_application(auth_client, sample_master_profile):
    auth_client.post('/api/v1/resume/profiles', json={
        'profile_data': sample_master_profile,
        'source_type': 'manual',
    })
    posting = auth_client.post('/api/v1/jobs/postings', json={
        'title': 'Engineer',
        'company': 'TestCo',
        'description': 'Python role',
    }).get_json()
    application = auth_client.post('/api/v1/applications/', json={
        'job_posting_id': posting['id'],
    }).get_json()

    resp = auth_client.delete(f"/api/v1/applications/{application['id']}")
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    listed = auth_client.get('/api/v1/applications/').get_json()
    assert all(a['id'] != application['id'] for a in listed['data'])

    resp = auth_client.delete(f"/api/v1/jobs/postings/{posting['id']}")
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True

    listed = auth_client.get('/api/v1/jobs/postings').get_json()
    assert all(p['id'] != posting['id'] for p in listed['data'])
