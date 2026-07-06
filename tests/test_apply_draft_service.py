"""Tests for apply draft service."""

from app.models.jobs import ApplyDraft
from app.services.apply_draft_service import apply_draft_service


def test_is_complete_requires_email():
    assert apply_draft_service.is_complete(None) is False
    assert apply_draft_service.is_complete(ApplyDraft(form_fields={'full_name': 'Jane'})) is False
    assert apply_draft_service.is_complete(ApplyDraft(form_fields={'email': 'jane@example.com'})) is True
