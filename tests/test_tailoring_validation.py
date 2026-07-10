"""Tests for tailoring diff validation."""

from app.services.tailoring_service import tailoring_service


def test_validate_diff_rejects_orphan_bullet_refs(sample_master_profile):
    diff_log = [
        {'field': 'experience.bullet', 'master_ref': 'b1', 'action': 'rephrase'},
        {'field': 'experience.bullet', 'master_ref': 'invalid-id', 'action': 'rephrase'},
    ]
    errors = tailoring_service.validate_diff(diff_log, sample_master_profile)
    assert any('invalid-id' in e for e in errors)


def test_validate_diff_accepts_valid_refs(sample_master_profile):
    diff_log = [
        {'field': 'experience.bullet', 'master_ref': 'b1', 'action': 'rephrase'},
        {'field': 'experience.bullet', 'master_ref': 'b2', 'action': 'rephrase'},
    ]
    errors = tailoring_service.validate_diff(diff_log, sample_master_profile)
    assert errors == []


def test_tailor_for_job_with_coverage(sample_master_profile):
    jd = 'Looking for Python Flask engineer with SQL experience and REST APIs.'
    tailored, diff_log, coverage = tailoring_service.tailor_for_job_with_coverage(
        sample_master_profile,
        'Backend Engineer',
        jd,
        'Acme Corp',
    )
    assert tailored is not None
    assert isinstance(diff_log, list)
    assert coverage >= 0


def test_tailor_skips_bullet_inserts_without_approved_keywords(sample_master_profile, monkeypatch):
    """Empty approved_keywords must not invent claims via LLM rephrase."""
    from unittest.mock import MagicMock

    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)

    mock_rephrase = MagicMock(return_value='Built Python APIs with Flask and Kubernetes')
    monkeypatch.setattr(
        'app.services.tailoring_service.llm_service.rephrase_bullet',
        mock_rephrase,
    )
    profile = dict(sample_master_profile)
    profile['approved_keywords'] = []
    jd = 'Looking for Kubernetes and Terraform experience with Python Flask.'
    tailored, diff_log = tailoring_service.tailor_for_job(profile, 'Backend Engineer', jd)
    assert mock_rephrase.call_count == 0
    assert not any(c.get('action') == 'rephrase' for c in diff_log)
    assert tailored['experience'][0]['bullets'][0]['text'] == 'Built Python APIs with Flask'


def test_tailor_only_inserts_approved_keywords(sample_master_profile, monkeypatch):
    def fake_rephrase(text, keyword, job_title=''):
        return f'{text} ({keyword})'

    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setattr(
        'app.services.tailoring_service.llm_service.rephrase_bullet',
        fake_rephrase,
    )
    profile = dict(sample_master_profile)
    profile['approved_keywords'] = ['Kubernetes']
    jd = (
        'Must have Kubernetes and Ziglang experience. '
        'Python Flask preferred. Terraform nice to have.'
    )
    tailored, diff_log = tailoring_service.tailor_for_job(profile, 'Backend Engineer', jd)
    rephrases = [c for c in diff_log if c.get('action') == 'rephrase']
    assert rephrases
    assert all(c.get('keyword_added', '').lower() == 'kubernetes' for c in rephrases)
    assert 'Ziglang' not in str(tailored)
    assert 'Terraform' not in [c.get('keyword_added') for c in rephrases]


def test_filter_insertable_keywords_substring():
    missing = ['kubernetes', 'ci/cd pipelines', 'cobol']
    profile = {'approved_keywords': ['Kubernetes', 'CI/CD']}
    assert tailoring_service.filter_insertable_keywords(missing, profile) == [
        'kubernetes',
        'ci/cd pipelines',
    ]
