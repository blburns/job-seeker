"""Tests for cover letter regeneration status handling."""

from unittest.mock import MagicMock, patch

from app.services.apply_draft_service import ApplyDraftService


def _profile_patch():
    return patch('app.services.apply_draft_service.MasterProfile')


def test_regenerate_keeps_retrying_until_timeout(monkeypatch):
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'
    monkeypatch.setenv('COVER_LETTER_RETRY_MAX', '0')
    monkeypatch.setenv('COVER_LETTER_RETRY_BASE_SECONDS', '1')
    monkeypatch.setenv('COVER_LETTER_RETRY_TIMEOUT_SECONDS', '3')

    # Force timeout after a couple of sleeps by advancing monotonic time.
    times = [0.0, 0.5, 1.0, 1.5, 2.0, 3.5]

    def fake_monotonic():
        return times.pop(0) if times else 99.0

    with patch.object(ApplyDraftService, 'ensure_draft', return_value=draft), \
         patch.object(
             ApplyDraftService,
             '_generate_cover_letter',
             side_effect=RuntimeError('Gemini rate limit / quota exceeded (HTTP 429)'),
         ), \
         patch('app.services.apply_draft_service.time.sleep') as mock_sleep, \
         patch('app.services.apply_draft_service.time.monotonic', side_effect=fake_monotonic), \
         _profile_patch() as MockProfile:
        MockProfile.query.filter_by.return_value.first.return_value = MagicMock(
            profile_data={'contact': {'name': 'Jane'}}
        )
        application = MagicMock()
        application.job_posting = MagicMock(title='Eng', company='Acme')
        result = ApplyDraftService.regenerate_cover_letter(application, 'user-1')

    assert result['ok'] is False
    assert result['rate_limited'] is True
    assert result['timed_out'] is True
    assert result['retried'] is True
    assert mock_sleep.call_count >= 1
    assert draft.cover_letter == 'Previous letter'


def test_regenerate_cover_letter_succeeds_after_retry(monkeypatch):
    draft = MagicMock()
    draft.cover_letter = 'Previous letter'
    monkeypatch.setenv('COVER_LETTER_RETRY_MAX', '0')
    monkeypatch.setenv('COVER_LETTER_RETRY_BASE_SECONDS', '1')
    monkeypatch.setenv('COVER_LETTER_RETRY_TIMEOUT_SECONDS', '600')

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
    assert result['timed_out'] is False
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
