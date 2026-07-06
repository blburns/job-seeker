"""Tests for tailoring diff reporting."""

from app.services.tailoring_diff_service import tailoring_diff_service


def test_summarize_diff_log():
    diff_log = [
        {'field': 'experience.bullet', 'action': 'rephrase', 'keyword_added': 'python'},
        {'field': 'skills.technical', 'action': 'reorder'},
        {'_meta': True, 'coverage_before': 40, 'coverage_after': 55},
    ]
    summary = tailoring_diff_service.summarize(diff_log)
    assert summary['total_changes'] == 2
    assert summary['rephrased_bullets'] == 1
    assert summary['keywords_added'] == ['python']


def test_coverage_delta_from_meta():
    diff_log = [
        {'_meta': True, 'coverage_before': 40.0, 'coverage_after': 62.5},
    ]
    delta = tailoring_diff_service.coverage_delta(diff_log)
    assert delta['before'] == 40.0
    assert delta['after'] == 62.5
    assert delta['delta'] == 22.5


def test_export_text_includes_before_after():
    diff_log = [
        {
            'field': 'experience.bullet',
            'action': 'rephrase',
            'role': 'Engineer @ Acme',
            'old': 'Built APIs',
            'new': 'Built Python APIs',
            'keyword_added': 'python',
        }
    ]
    text = tailoring_diff_service.export_text(diff_log, 'Backend Engineer', 'Acme')
    assert 'Built APIs' in text
    assert 'Built Python APIs' in text
    assert 'python' in text


def test_build_compare_detects_headline_change():
    master = {'headline': 'Software Engineer', 'experience': [], 'skills': {'technical': []}}
    tailored = {'headline': 'Python Developer', 'experience': [], 'skills': {'technical': []}}
    compare = tailoring_diff_service.build_compare(master, tailored)
    assert compare['headline']['changed'] is True
    assert tailoring_diff_service.compare_has_changes(compare) is True


def test_build_overview_narrative_and_checklist():
    diff_log = [
        {
            'field': 'headline',
            'action': 'set',
            'old': 'Software Engineer',
            'new': 'Python Developer',
        },
        {
            'field': 'experience.bullet',
            'action': 'rephrase',
            'role': 'Engineer @ Acme',
            'old': 'Built APIs',
            'new': 'Built Python APIs',
            'keyword_added': 'python',
        },
        {
            '_meta': True,
            'coverage_before': 40,
            'coverage_after': 55,
            'matched_before': ['python'],
            'matched_after': ['python', 'flask'],
            'missing_after': ['kubernetes'],
        },
    ]
    compare = {
        'headline': {'master': 'Software Engineer', 'tailored': 'Python Developer', 'changed': True},
        'summary': {'master': '', 'tailored': '', 'changed': False},
        'skills': {'master': [], 'tailored': [], 'changed': False},
        'experience': [],
    }
    overview = tailoring_diff_service.build_overview(
        diff_log, compare=compare, job_title='Python Developer',
    )
    assert 'Python Developer' in overview['narrative']
    assert overview['total_changes'] == 2
    assert len(overview['checklist']) >= 2
    assert len(overview['highlights']) >= 1

