"""Tests for rejecting individual tailoring changes."""

import copy

from app.services.llm_service import LLMService
from app.services.tailoring_diff_service import tailoring_diff_service
from app.services.tailoring_service import tailoring_service


def test_heuristic_rephrase_does_not_invent_keywords(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    original = 'Built APIs for internal tools.'
    assert LLMService.rephrase_bullet(original, 'Kubernetes', 'SRE') == original


def test_reject_rephrase_restores_bullet(sample_master_profile):
    tailored = copy.deepcopy(sample_master_profile)
    tailored['experience'][0]['bullets'][0]['text'] = (
        'Built Python APIs with Flask, including Kubernetes.'
    )
    diff_log = [
        {
            'field': 'headline',
            'action': 'set',
            'old': 'Software Engineer',
            'new': 'Backend Engineer',
        },
        {
            'field': 'experience.bullet',
            'action': 'rephrase',
            'master_ref': 'b1',
            'role': 'Engineer @ Acme',
            'old': 'Built Python APIs with Flask',
            'new': 'Built Python APIs with Flask, including Kubernetes.',
            'keyword_added': 'Kubernetes',
        },
    ]

    updated, updated_log = tailoring_service.reject_change(tailored, diff_log, 1)
    assert updated['experience'][0]['bullets'][0]['text'] == 'Built Python APIs with Flask'
    assert updated_log[1]['rejected'] is True
    assert updated_log[0].get('rejected') is not True

    summary = tailoring_diff_service.summarize(updated_log)
    assert summary['rephrased_bullets'] == 0
    assert summary['rejected_changes'] == 1
    assert summary['field_updates'] == 1


def test_reject_headline_restores_old(sample_master_profile):
    tailored = copy.deepcopy(sample_master_profile)
    tailored['headline'] = 'Staff Engineer'
    diff_log = [
        {
            'field': 'headline',
            'action': 'set',
            'old': 'Software Engineer',
            'new': 'Staff Engineer',
        },
    ]
    updated, updated_log = tailoring_service.reject_change(tailored, diff_log, 0)
    assert updated['headline'] == 'Software Engineer'
    assert updated_log[0]['rejected'] is True


def test_reject_already_rejected_raises(sample_master_profile):
    tailored = copy.deepcopy(sample_master_profile)
    diff_log = [
        {
            'field': 'headline',
            'action': 'set',
            'old': 'Software Engineer',
            'new': 'Staff Engineer',
            'rejected': True,
        },
    ]
    try:
        tailoring_service.reject_change(tailored, diff_log, 0)
        assert False, 'expected ValueError'
    except ValueError as exc:
        assert 'already rejected' in str(exc).lower()
