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
