"""Smoke and unit tests for apply adapters."""

from unittest.mock import MagicMock

from app.services.apply_adapters.base import ApplyContext
from app.services.apply_adapters.generic import GenericAdapter
from app.services.apply_adapters.greenhouse import GreenhouseAdapter
from app.services.apply_adapters.linkedin import LinkedInAdapter
from app.services.apply_adapters.registry import submit_application


def _context(**overrides):
    data = dict(
        application_id='test-id',
        job_url='https://boards.greenhouse.io/acme/jobs/1',
        job_title='Engineer',
        company='Acme',
        resume_path='',
        form_fields={'full_name': 'Jane Doe', 'email': 'a@b.com', 'phone': '555-0100'},
        user_id='user-1',
    )
    data.update(overrides)
    return ApplyContext(**data)


def test_generic_adapter_needs_manual():
    adapter = GenericAdapter()
    result = adapter.submit(_context(job_url='https://example.com/careers'))
    assert result.status == 'needs_manual'
    assert result.success is False


def test_greenhouse_can_handle():
    adapter = GreenhouseAdapter()
    assert adapter.can_handle('https://boards.greenhouse.io/acme/jobs/1')
    assert not adapter.can_handle('https://example.com')


def test_greenhouse_disabled_without_flag(monkeypatch):
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'false')
    result = GreenhouseAdapter().submit(_context())
    assert result.status == 'needs_manual'
    assert 'disabled' in result.message.lower()


def test_detect_confirmation_from_url():
    assert GreenhouseAdapter.detect_confirmation(
        'https://boards.greenhouse.io/acme/jobs/1/confirmation',
        '',
    )
    assert GreenhouseAdapter.detect_confirmation(
        'https://boards.greenhouse.io/acme/thanks',
        '',
    )


def test_detect_confirmation_from_body_text():
    assert GreenhouseAdapter.detect_confirmation(
        'https://boards.greenhouse.io/acme/jobs/1',
        'Thank you for your application! We have received your application.',
    )
    assert not GreenhouseAdapter.detect_confirmation(
        'https://boards.greenhouse.io/acme/jobs/1',
        'Please fill out the application form below.',
    )


def test_click_submit_tries_selectors():
    page = MagicMock()
    fail_loc = MagicMock()
    fail_loc.count.return_value = 0
    ok_loc = MagicMock()
    ok_loc.count.return_value = 1
    page.locator.side_effect = lambda _sel: MagicMock(first=fail_loc if page.locator.call_count == 1 else ok_loc)

    # Simpler: first call returns empty, second returns clickable
    calls = {'n': 0}

    def locator(_sel):
        calls['n'] += 1
        loc = MagicMock()
        if calls['n'] == 1:
            loc.count.return_value = 0
            loc.click.side_effect = Exception('not found')
        else:
            loc.count.return_value = 1
        wrapper = MagicMock()
        wrapper.first = loc
        return wrapper

    page.locator.side_effect = locator
    assert GreenhouseAdapter.click_submit(page) is True


def test_greenhouse_run_on_page_submitted(tmp_path, monkeypatch):
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'true')
    adapter = GreenhouseAdapter()
    page = MagicMock()
    page.url = 'https://boards.greenhouse.io/acme/jobs/1/confirmation'
    page.inner_text.return_value = 'Thank you for applying'

    loc = MagicMock()
    loc.count.return_value = 1
    page.locator.return_value.first = loc

    proof = str(tmp_path / 'proof.png')
    result = adapter._run_on_page(page, _context(), proof)
    assert result.status == 'submitted'
    assert result.success is True
    loc.click.assert_called()


def test_greenhouse_run_on_page_needs_manual_without_confirm(tmp_path, monkeypatch):
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'true')
    adapter = GreenhouseAdapter()
    page = MagicMock()
    page.url = 'https://boards.greenhouse.io/acme/jobs/1'
    page.inner_text.return_value = 'Application form'
    loc = MagicMock()
    loc.count.return_value = 1
    page.locator.return_value.first = loc

    result = adapter._run_on_page(page, _context(), str(tmp_path / 'proof.png'))
    assert result.status == 'needs_manual'
    assert result.success is False
    assert 'confirmation' in result.message.lower()


def test_linkedin_requires_credentials():
    adapter = LinkedInAdapter()
    result = adapter.submit(_context(
        job_url='https://www.linkedin.com/jobs/view/123',
        form_fields={},
        portal_credentials=None,
    ))
    assert result.status == 'needs_manual'


def test_submit_application_uses_registry(monkeypatch):
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'false')
    result = submit_application(_context())
    assert result.status in ('needs_manual', 'failed', 'submitted')
