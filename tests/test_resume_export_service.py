"""Tests for resume preview export."""

from app.services.resume_export_service import resume_export_service


def test_render_preview_text_includes_sections():
    profile = {
        'contact': {'name': 'Jane Doe', 'email': 'jane@example.com'},
        'headline': 'Python Developer',
        'summary_variants': [{'text': 'Backend engineer with 8 years experience.'}],
        'experience': [{
            'title': 'Engineer',
            'company': 'Acme',
            'start': '2020',
            'end': 'Present',
            'bullets': [{'text': 'Built Python APIs'}],
        }],
        'skills': {'technical': ['Python', 'Flask']},
    }
    text = resume_export_service.render_preview_text(profile)
    assert 'JANE DOE' in text
    assert 'SUMMARY' in text
    assert 'EXPERIENCE' in text
    assert 'SKILLS' in text
    assert 'Python APIs' in text


def test_export_cover_letter_docx():
    content, name = resume_export_service.export_cover_letter_docx(
        'Dear Hiring Manager,\n\nI am interested.\n\nSincerely,\nJane',
        'Test_Cover.docx',
    )
    assert name == 'Test_Cover.docx'
    assert len(content) > 100
