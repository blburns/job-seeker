"""Unit tests for resume parser service."""

import pytest

from app.services.resume_parser_service import resume_parser_service


SAMPLE_RESUME_TXT = """
Jane Doe
jane@example.com | 555-0100 | Remote
linkedin.com/in/janedoe

SUMMARY
Experienced software engineer specializing in Python backends.

EXPERIENCE
Senior Engineer | Acme Corp | 2020 - Present
• Built Python APIs with Flask and PostgreSQL
• Led migration to AWS and Docker
• Mentored a team of 3 engineers

Software Engineer | Beta Inc | 2017 - 2020
• Developed REST services in Python
• Improved CI/CD pipelines with GitHub Actions

EDUCATION
BS Computer Science - State University | 2017

SKILLS
Python, Flask, PostgreSQL, AWS, Docker, Git
"""


def test_parse_text_extracts_contact_and_sections():
    profile = resume_parser_service.parse_text(SAMPLE_RESUME_TXT)
    assert profile['contact'].get('email') == 'jane@example.com'
    assert 'Jane' in (profile['contact'].get('name') or '')
    assert profile.get('experience')
    assert len(profile['experience']) >= 1
    assert profile['experience'][0].get('bullets')


def test_parse_file_txt():
    profile, confidence = resume_parser_service.parse_file(
        SAMPLE_RESUME_TXT.encode('utf-8'),
        'resume.txt',
    )
    assert confidence > 0
    assert profile['contact'].get('email')
    assert profile.get('experience')


def test_parse_file_unsupported_type():
    with pytest.raises(ValueError, match='Unsupported'):
        resume_parser_service.parse_file(b'not a resume', 'resume.xyz')


def test_validate_profile_requires_contact_and_experience():
    errors = resume_parser_service.validate_profile({})
    assert any('name' in e.lower() for e in errors)
    assert any('email' in e.lower() for e in errors)
    assert any('experience' in e.lower() for e in errors)


def test_validate_profile_accepts_complete(sample_master_profile):
    errors = resume_parser_service.validate_profile(sample_master_profile)
    assert errors == []


def test_parse_empty_text_returns_structure():
    profile = resume_parser_service.parse_text('')
    assert isinstance(profile, dict)
    assert 'contact' in profile
