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
    profile, confidence, warnings = resume_parser_service.parse_file(
        SAMPLE_RESUME_TXT.encode('utf-8'),
        'resume.txt',
    )
    assert confidence > 0
    assert profile['contact'].get('email')
    assert profile.get('experience')
    assert warnings == []


def test_parse_file_unsupported_type():
    with pytest.raises(ValueError, match='Unsupported'):
        resume_parser_service.parse_file(b'not a resume', 'resume.xyz')


def test_detect_multi_column_heuristic():
    # Two clusters of words with a sparse gutter
    words = []
    for i in range(20):
        words.append({'text': f'L{i}', 'x0': 40.0, 'top': float(i * 12)})
        words.append({'text': f'R{i}', 'x0': 320.0, 'top': float(i * 12)})
    assert resume_parser_service._detect_multi_column(words, page_width=400.0) is True
    single = [{'text': f'W{i}', 'x0': 50.0 + (i % 5) * 10, 'top': float(i * 10)} for i in range(50)]
    assert resume_parser_service._detect_multi_column(single, page_width=400.0) is False


def test_extract_pdf_tables_flattens_rows():
    class FakePage:
        def extract_tables(self):
            return [
                [['Python', 'Flask'], ['AWS', 'Docker']],
                [[None, ''], ['Skills', 'SQL']],
            ]

    text = resume_parser_service._extract_pdf_tables(FakePage())
    assert 'Python | Flask' in text
    assert 'AWS | Docker' in text
    assert 'Skills | SQL' in text


def test_get_parse_diagnostics_includes_extraction_warnings(sample_master_profile):
    hints = resume_parser_service.get_parse_diagnostics(
        sample_master_profile,
        ['Detected multi-column layout on 1 page(s).'],
    )
    assert hints[0].startswith('Detected multi-column')


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
