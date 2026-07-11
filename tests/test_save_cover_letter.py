"""Tests for saving cover letter drafts."""

from werkzeug.datastructures import MultiDict

from app.extensions.core import db
from app.models.jobs import Application, ApplicationStage, ApplyDraft, JobPosting


def _seed_application_with_draft(db_session, test_user):
    posting = JobPosting(
        user_id=test_user.id,
        title='Engineer',
        company='Acme',
        description='Build things',
        url='https://example.com/jobs/1',
        source='manual',
    )
    db_session.add(posting)
    db_session.flush()
    app_record = Application(
        user_id=test_user.id,
        job_posting_id=posting.id,
        stage=ApplicationStage.READY_TO_APPLY.value,
        portal_url=posting.url,
    )
    db_session.add(app_record)
    db_session.flush()
    draft = ApplyDraft(
        application_id=app_record.id,
        user_id=test_user.id,
        form_fields={
            'full_name': 'Jane Doe',
            'email': 'jane@example.com',
            'cover_letter': '',  # legacy empty field that used to clobber saves
        },
        cover_letter='Original letter',
        status='draft',
    )
    db_session.add(draft)
    db_session.commit()
    return app_record, draft


def test_save_cover_letter_uses_textarea_not_legacy_hidden(auth_client, db_session, test_user):
    app_record, draft = _seed_application_with_draft(db_session, test_user)
    edited = 'Dear Hiring Manager,\n\nI edited this letter.\n\nSincerely,\nJane'

    # Mimic the broken form: hidden cover_letter='' then textarea with edits.
    data = MultiDict([
        ('full_name', 'Jane Doe'),
        ('email', 'jane@example.com'),
        ('cover_letter', ''),
        ('cover_letter', edited),
    ])
    resp = auth_client.post(
        f'/apply/{app_record.id}/save-draft',
        data=data,
        follow_redirects=False,
        headers={'Referer': f'/applications/{app_record.id}/tailoring?tab=cover'},
    )
    assert resp.status_code == 302

    db.session.refresh(draft)
    assert draft.cover_letter == edited
    assert 'cover_letter' not in (draft.form_fields or {})


def test_build_apply_draft_omits_cover_letter_field():
    from app.services.job_discovery_service import job_discovery_service

    fields = job_discovery_service.build_apply_draft(
        {'contact': {'name': 'A', 'email': 'a@b.com'}, 'experience': []},
        {'title': 'Eng', 'company': 'Co', 'url': 'https://x'},
    )
    assert 'cover_letter' not in fields
    assert fields['email'] == 'a@b.com'
