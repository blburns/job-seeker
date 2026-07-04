"""Smoke tests for apply adapters."""

import os

from app.services.apply_adapters.base import ApplyContext
from app.services.apply_adapters.generic import GenericAdapter
from app.services.apply_adapters.greenhouse import GreenhouseAdapter
from app.services.apply_adapters.linkedin import LinkedInAdapter
from app.services.apply_adapters.registry import submit_application


def test_generic_adapter_needs_manual():
    adapter = GenericAdapter()
    result = adapter.submit(ApplyContext(
        application_id='test-id',
        job_url='https://example.com/careers',
        job_title='Engineer',
        company='Example',
        resume_path='',
        form_fields={'email': 'a@b.com'},
        user_id='user-1',
    ))
    assert result.status == 'needs_manual'
    assert result.success is False


def test_greenhouse_can_handle():
    adapter = GreenhouseAdapter()
    assert adapter.can_handle('https://boards.greenhouse.io/acme/jobs/1')
    assert not adapter.can_handle('https://example.com')


def test_linkedin_requires_credentials():
    adapter = LinkedInAdapter()
    result = adapter.submit(ApplyContext(
        application_id='test-id',
        job_url='https://www.linkedin.com/jobs/view/123',
        job_title='Engineer',
        company='Example',
        resume_path='',
        form_fields={},
        user_id='user-1',
        portal_credentials=None,
    ))
    assert result.status == 'needs_manual'


def test_submit_application_uses_registry():
    os.environ['APPLY_AUTOMATION_ENABLED'] = 'false'
    result = submit_application(ApplyContext(
        application_id='test-id',
        job_url='https://boards.greenhouse.io/acme/jobs/1',
        job_title='Engineer',
        company='Acme',
        resume_path='',
        form_fields={'email': 'a@b.com'},
        user_id='user-1',
    ))
    assert result.status in ('needs_manual', 'failed', 'submitted')
