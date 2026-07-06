"""Tests for job detail enrichment helpers."""

from types import SimpleNamespace

from app.services.scraping.job_detail_enrichment import JobDetailEnrichment


def test_needs_enrichment_always_for_indeed_without_full_description():
    job = SimpleNamespace(
        source='indeed',
        url='https://www.indeed.com/viewjob?jk=abc',
        description='Short snippet from search results card.',
        company='Acme',
        location='Austin, TX',
    )
    assert JobDetailEnrichment.needs_enrichment(job) is True


def test_needs_enrichment_skips_indeed_with_full_description():
    job = SimpleNamespace(
        source='indeed',
        url='https://www.indeed.com/viewjob?jk=abc',
        description='x' * 500,
        company='Acme',
        location='Austin, TX',
    )
    assert JobDetailEnrichment.needs_enrichment(job) is False


def test_merge_prefers_longer_description():
    base = {'description': 'short snippet'}
    enriched = {'description': 'x' * 200}
    merged = JobDetailEnrichment._merge(base, enriched)
    assert len(merged['description']) == 200


def test_keyword_text_includes_title_and_company():
    text = JobDetailEnrichment.keyword_text(
        title='Python Developer',
        company='Acme Corp',
        location='Remote',
        description='',
    )
    assert 'Python Developer' in text
    assert 'Acme Corp' in text


def test_needs_posting_enrichment_for_sparse_indeed_posting():
    posting = SimpleNamespace(
        source='indeed',
        url='https://www.indeed.com/viewjob?jk=abc',
        description='',
    )
    assert JobDetailEnrichment.needs_posting_enrichment(posting) is True
