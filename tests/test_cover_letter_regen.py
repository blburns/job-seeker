"""Tests for cover letter regeneration status handling."""

from unittest.mock import MagicMock, patch

from app.services.apply_draft_service import ApplyDraftService


def test_regenerate_cover_letter_reports_rate_limit():
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             side_effect=RuntimeError('Gemini rate limit / quota exceeded (HTTP 429)'),
         ), \
         patch('app.services.apply_draft_service.MasterProfile') as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is False
    assert result['rate_limited'] is True
    assert draft.cover_letter == 'Previous letter'


def test_regenerate_cover_letter_success():
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             return_value='Fresh AI letter',
         ), \
         patch('app.services.apply_draft_service.MasterProfile') as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is True
    assert draft.cover_letter == 'Fresh AI letter'
