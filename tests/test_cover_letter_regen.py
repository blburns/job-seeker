"""Tests for cover letter regeneration status handling."""

from unittest.mock import MagicMock, patch

from app.services.apply_draft_service import ApplyDraftService


def _profile_patch():
    return patch('app.services.apply_draft_service.MasterProfile')


def test_regenerate_cover_letter_retries_then_reports_rate_limit(monkeypatch):
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'
    monkeypatch.setenv('COVER_LETTER_RETRY_MAX', '3')
    monkeypatch.setenv('COVER_LETTER_RETRY_BASE_SECONDS', '1')

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             side_effect=RuntimeError('Gemini rate limit / quota exceeded (HTTP 429)'),
         ), \
         patch('app.services.apply_draft_service.time.sleep') as mock_sleep, \
         _profile_patch() as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is False
    assert result['rate_limited'] is True
    assert result['attempts'] == 3
    assert result['retried'] is True
    assert mock_sleep.call_count == 2
    assert draft.cover_letter == 'Previous letter'


def test_regenerate_cover_letter_succeeds_after_retry(monkeypatch):
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'
    monkeypatch.setenv('COVER_LETTER_RETRY_MAX', '4')
    monkeypatch.setenv('COVER_LETTER_RETRY_BASE_SECONDS', '1')

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             side_effect=[
                 RuntimeError('Gemini rate limit / quota exceeded (HTTP 429)'),
                 RuntimeError('Gemini rate limit / quota exceeded (HTTP 429)'),
                 'Fresh AI letter after wait',
             ],
         ), \
         patch('app.services.apply_draft_service.time.sleep') as mock_sleep, \
         _profile_patch() as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is True
    assert result['attempts'] == 3
    assert result['retried'] is True
    assert mock_sleep.call_count == 2
    assert draft.cover_letter == 'Fresh AI letter after wait'


def test_regenerate_cover_letter_success():
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             return_value='Fresh AI letter',
         ), \
         _profile_patch() as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is True
    assert result['retried'] is False
    assert draft.cover_letter == 'Fresh AI letter'
