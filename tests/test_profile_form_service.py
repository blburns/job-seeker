"""Tests for manual master profile form serialization."""

from werkzeug.datastructures import ImmutableMultiDict

from app.services.profile_form_service import profile_form_service
from app.services.resume_export_service import resume_export_service


def test_build_profile_summary_variants_are_dicts():
    form_data = ImmutableMultiDict({
        'contact_name': 'Jane Doe',
        'summary': 'Experienced engineer building APIs.',
    })
    profile = profile_form_service.build_profile_from_form(form_data)
    assert len(profile['summary_variants']) == 1
    variant = profile['summary_variants'][0]
    assert isinstance(variant, dict)
    assert variant['text'] == 'Experienced engineer building APIs.'
    assert variant['id']


def test_build_profile_includes_approved_keywords():
    form_data = ImmutableMultiDict({
        'contact_name': 'Jane Doe',
        'contact_email': 'jane@example.com',
        'approved_keywords': 'Kubernetes, CI/CD, GraphQL',
        'skills_technical': 'Python, Flask',
    })
    profile = profile_form_service.build_profile_from_form(form_data)
    assert profile['approved_keywords'] == ['Kubernetes', 'CI/CD', 'GraphQL']
    assert profile['skills']['technical'] == ['Python', 'Flask']


def test_profile_to_form_context_round_trips_approved_keywords():
    ctx = profile_form_service.profile_to_form_context({
        'contact': {},
        'approved_keywords': ['Terraform', 'Docker'],
        'skills': {'technical': ['Python'], 'soft': [], 'certifications': []},
        'experience': [],
        'education': [],
    })
    assert ctx['approved_keywords'] == 'Terraform, Docker'


def test_export_docx_handles_string_summary_variants():
    """Legacy profiles may store summary_variants as plain strings."""
    profile = {
        'contact': {'name': 'Jane Doe', 'email': 'jane@example.com'},
        'headline': 'Software Engineer',
        'summary_variants': ['Legacy summary text'],
        'experience': [],
        'education': [],
        'skills': {},
    }
    docx_bytes, _ = resume_export_service.export_docx(profile)
    assert docx_bytes
    assert b'PK' in docx_bytes[:4]  # DOCX zip header
