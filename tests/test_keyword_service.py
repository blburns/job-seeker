"""Unit tests for keyword extraction and coverage analysis."""

from app.services.keyword_service import keyword_service


def test_extract_keywords_finds_tech_terms():
    text = (
        'Looking for a Python engineer with Flask, PostgreSQL, Docker, and AWS. '
        'Kubernetes experience is a plus. Must know REST APIs.'
    )
    keywords = keyword_service.extract_keywords(text)
    lower = {k.lower() for k in keywords}
    assert 'python' in lower
    assert 'flask' in lower
    assert 'postgresql' in lower or 'postgres' in lower
    assert 'docker' in lower
    assert 'aws' in lower


def test_extract_keywords_empty_text():
    assert keyword_service.extract_keywords('') == []
    assert keyword_service.extract_keywords(None) == []


def test_analyze_coverage_matched_and_missing(sample_master_profile):
    jd = (
        'Senior Python Engineer with Flask and AWS experience. '
        'Kubernetes and GraphQL required.'
    )
    result = keyword_service.analyze_coverage(jd, sample_master_profile)
    assert 'python' in result['matched_keywords'] or 'flask' in result['matched_keywords']
    assert isinstance(result['missing_keywords'], list)
    assert 0 <= result['coverage_score'] <= 100
    assert result['jd_keywords']


def test_synonym_match_javascript():
    profile = {
        'contact': {'name': 'A', 'email': 'a@b.com'},
        'experience': [{'title': 'Dev', 'company': 'X', 'bullets': [{'text': 'Built JS frontends'}]}],
        'skills': {'technical': ['js'], 'certifications': []},
    }
    result = keyword_service.analyze_coverage('Need JavaScript developer', profile)
    # js should match javascript via synonym or direct profile text
    assert result['coverage_score'] > 0 or result['matched_keywords'] or result['synonym_matches']


def test_profile_to_text_includes_skills(sample_master_profile):
    text = keyword_service.profile_to_text(sample_master_profile)
    assert 'python' in text
    assert 'flask' in text
    assert 'acme' in text
