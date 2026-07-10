"""Build tailoring reports, comparisons, and exports from diff logs."""

from collections import Counter
from typing import Any, Dict, List, Optional


class TailoringDiffService:
    @classmethod
    def is_meta(cls, change: Dict[str, Any]) -> bool:
        return bool(change.get('_meta')) or change.get('field') == '_meta'

    @classmethod
    def get_meta(cls, diff_log: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        for change in diff_log or []:
            if cls.is_meta(change):
                return change
        return {}

    @classmethod
    def get_changes(
        cls,
        diff_log: Optional[List[Dict[str, Any]]],
        include_rejected: bool = False,
    ) -> List[Dict[str, Any]]:
        changes = []
        for change in diff_log or []:
            if cls.is_meta(change):
                continue
            if change.get('rejected') and not include_rejected:
                continue
            changes.append(change)
        return changes

    @classmethod
    def summarize(cls, diff_log: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        changes = cls.get_changes(diff_log)
        counts = Counter(change.get('action', 'unknown') for change in changes)
        keywords_added = [
            change['keyword_added']
            for change in changes
            if change.get('keyword_added')
        ]
        rejected_count = sum(
            1 for change in (diff_log or [])
            if not cls.is_meta(change) and change.get('rejected')
        )
        return {
            'total_changes': len(changes),
            'rephrased_bullets': counts.get('rephrase', 0),
            'reordered_sections': counts.get('reorder', 0),
            'summary_updates': counts.get('select_variant', 0),
            'field_updates': counts.get('set', 0),
            'keywords_added': keywords_added,
            'rejected_changes': rejected_count,
        }

    @classmethod
    def coverage_delta(cls, diff_log: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, float]]:
        meta = cls.get_meta(diff_log)
        before = meta.get('coverage_before')
        after = meta.get('coverage_after')
        if before is None or after is None:
            return None
        return {
            'before': float(before),
            'after': float(after),
            'delta': round(float(after) - float(before), 1),
        }

    @classmethod
    def keyword_impact(
        cls,
        diff_log: Optional[List[Dict[str, Any]]],
        jd_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        meta = cls.get_meta(diff_log)
        matched_before = set(meta.get('matched_before') or [])
        matched_after = set(meta.get('matched_after') or [])
        newly_matched = sorted(matched_after - matched_before)
        still_missing = sorted(set(jd_keywords or meta.get('missing_after') or []) - matched_after)
        return {
            'newly_matched': newly_matched,
            'still_missing': still_missing,
            'matched_before_count': len(matched_before),
            'matched_after_count': len(matched_after),
        }

    @classmethod
    def build_compare(cls, master_data: Dict[str, Any], tailored_data: Dict[str, Any]) -> Dict[str, Any]:
        master_summary = cls._primary_summary(master_data)
        tailored_summary = cls._primary_summary(tailored_data)
        return {
            'headline': {
                'master': master_data.get('headline', ''),
                'tailored': tailored_data.get('headline', ''),
                'changed': master_data.get('headline') != tailored_data.get('headline'),
            },
            'summary': {
                'master': master_summary,
                'tailored': tailored_summary,
                'changed': master_summary != tailored_summary,
            },
            'skills': cls._compare_skills(
                master_data.get('skills', {}),
                tailored_data.get('skills', {}),
            ),
            'experience': cls._compare_experience(
                master_data.get('experience', []),
                tailored_data.get('experience', []),
            ),
        }

    @classmethod
    def build_overview(
        cls,
        diff_log: Optional[List[Dict[str, Any]]],
        compare: Optional[Dict[str, Any]] = None,
        keyword_impact: Optional[Dict[str, Any]] = None,
        job_title: str = '',
    ) -> Dict[str, Any]:
        summary = cls.summarize(diff_log)
        coverage = cls.coverage_delta(diff_log)
        compare = compare or {}
        keyword_impact = keyword_impact or {}
        changes = cls.get_changes(diff_log)

        narrative_parts = []
        if job_title:
            narrative_parts.append(f'targeting **{job_title}**')
        if summary['field_updates']:
            narrative_parts.append('updated the headline')
        if summary['summary_updates']:
            narrative_parts.append('picked a stronger summary variant')
        if summary['reordered_sections']:
            narrative_parts.append(
                f"reordered {summary['reordered_sections']} section(s) for keyword relevance"
            )
        if summary['rephrased_bullets']:
            kw = summary['keywords_added']
            kw_text = f" ({', '.join(kw)})" if kw else ''
            narrative_parts.append(
                f"rephrased {summary['rephrased_bullets']} bullet(s){kw_text}"
            )
        if not narrative_parts:
            narrative = 'Tailoring kept your master profile as-is — no material changes were needed.'
        else:
            narrative = 'Tailored your resume ' + ', '.join(narrative_parts) + '.'

        checklist = []
        headline = compare.get('headline', {})
        if headline.get('changed'):
            checklist.append({
                'label': 'Headline aligned to job title',
                'detail': f"{headline.get('master') or '—'} → {headline.get('tailored')}",
                'tab': 'compare',
            })
        summary_cmp = compare.get('summary', {})
        if summary_cmp.get('changed'):
            checklist.append({
                'label': 'Summary variant selected',
                'detail': 'Chose the variant that best matches job keywords.',
                'tab': 'compare',
            })
        for change in changes:
            if change.get('action') == 'reorder' and change.get('field') == 'experience':
                labels = change.get('new_labels') or []
                checklist.append({
                    'label': 'Experience reordered',
                    'detail': ' → '.join(labels[:4]) + ('…' if len(labels) > 4 else ''),
                    'tab': 'compare',
                })
                break
        for change in changes:
            if change.get('action') == 'reorder' and change.get('field') == 'skills.technical':
                new_skills = change.get('new') or []
                checklist.append({
                    'label': 'Skills reordered',
                    'detail': ', '.join(new_skills[:8]) + ('…' if len(new_skills) > 8 else ''),
                    'tab': 'compare',
                })
                break
        rephrase_count = summary['rephrased_bullets']
        if rephrase_count:
            checklist.append({
                'label': f'{rephrase_count} bullet(s) rephrased',
                'detail': 'Keywords added without inventing new experience.',
                'tab': 'rephrase',
            })
        if coverage:
            checklist.append({
                'label': 'Keyword coverage shifted',
                'detail': (
                    f"{coverage['before']}% → {coverage['after']}% "
                    f"({coverage['delta']:+.1f}%)"
                ),
                'tab': 'keywords',
            })
        newly_matched = keyword_impact.get('newly_matched') or []
        if newly_matched:
            checklist.append({
                'label': f'{len(newly_matched)} new keyword match(es)',
                'detail': ', '.join(newly_matched[:6]) + ('…' if len(newly_matched) > 6 else ''),
                'tab': 'keywords',
            })

        highlights = []
        for change in changes:
            action = change.get('action')
            field = change.get('field')
            if action == 'rephrase':
                highlights.append({
                    'kind': 'rephrase',
                    'title': change.get('role') or 'Bullet updated',
                    'badge': change.get('keyword_added'),
                    'before': change.get('old', ''),
                    'after': change.get('new', ''),
                })
            elif action == 'set' and field == 'headline' and change.get('old') != change.get('new'):
                highlights.append({
                    'kind': 'headline',
                    'title': 'Headline',
                    'before': change.get('old', ''),
                    'after': change.get('new', ''),
                })
            elif action == 'select_variant':
                highlights.append({
                    'kind': 'summary',
                    'title': 'Summary',
                    'before': (change.get('old') or '')[:160],
                    'after': (change.get('new') or '')[:160],
                })
            if len(highlights) >= 5:
                break

        return {
            'narrative': narrative.replace('**', ''),
            'checklist': checklist,
            'highlights': highlights,
            'total_changes': summary['total_changes'],
            'has_changes': summary['total_changes'] > 0 or bool(checklist),
        }

    @classmethod
    def compare_has_changes(cls, compare: Dict[str, Any]) -> bool:
        if compare.get('headline', {}).get('changed'):
            return True
        if compare.get('summary', {}).get('changed'):
            return True
        if compare.get('skills', {}).get('changed'):
            return True
        return any(row.get('changed') for row in compare.get('experience', []))

    @classmethod
    def export_text(
        cls,
        diff_log: Optional[List[Dict[str, Any]]],
        job_title: str = '',
        company: str = '',
    ) -> str:
        lines = [
            f'Tailoring report — {job_title} at {company}'.strip(' —'),
            '=' * 60,
            '',
        ]
        summary = cls.summarize(diff_log)
        coverage = cls.coverage_delta(diff_log)
        lines.append(f"Total changes: {summary['total_changes']}")
        lines.append(f"Rephrased bullets: {summary['rephrased_bullets']}")
        lines.append(f"Reordered sections: {summary['reordered_sections']}")
        if coverage:
            lines.append(
                f"Keyword coverage: {coverage['before']}% → {coverage['after']}% "
                f"({coverage['delta']:+.1f}%)"
            )
        if summary['keywords_added']:
            lines.append(f"Keywords added: {', '.join(summary['keywords_added'])}")
        lines.append('')
        lines.append('Changes')
        lines.append('-' * 60)

        for index, change in enumerate(cls.get_changes(diff_log), start=1):
            lines.append(f"{index}. [{change.get('action', '?')}] {change.get('field', '?')}")
            if change.get('role'):
                lines.append(f"   Role: {change['role']}")
            if change.get('keyword_added'):
                lines.append(f"   Keyword: {change['keyword_added']}")
            if change.get('old') is not None:
                lines.append(f"   Before: {change['old']}")
            if change.get('new') is not None:
                lines.append(f"   After: {change['new']}")
            if change.get('old_labels') and change.get('new_labels'):
                lines.append(f"   Order was: {' → '.join(change['old_labels'])}")
                lines.append(f"   Order now: {' → '.join(change['new_labels'])}")
            lines.append('')

        return '\n'.join(lines).strip() + '\n'

    @classmethod
    def _primary_summary(cls, profile: Dict[str, Any]) -> str:
        variants = profile.get('summary_variants') or []
        if variants:
            first = variants[0]
            if isinstance(first, dict):
                return first.get('text', '')
            return str(first)
        return profile.get('summary', '') or ''

    @classmethod
    def _compare_skills(cls, master_skills: Any, tailored_skills: Any) -> Dict[str, Any]:
        def normalize(skills: Any) -> List[str]:
            if isinstance(skills, dict):
                return list(skills.get('technical') or [])
            if isinstance(skills, list):
                return list(skills)
            return []

        master_list = normalize(master_skills)
        tailored_list = normalize(tailored_skills)
        return {
            'master': master_list,
            'tailored': tailored_list,
            'changed': master_list != tailored_list,
        }

    @classmethod
    def _compare_experience(
        cls,
        master_experience: List[Dict[str, Any]],
        tailored_experience: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        master_lookup = {entry.get('id'): entry for entry in master_experience if entry.get('id')}
        rows = []
        for entry in tailored_experience:
            entry_id = entry.get('id')
            master_entry = master_lookup.get(entry_id, entry)
            role = cls._role_label(entry)
            master_bullets = cls._bullet_texts(master_entry)
            tailored_bullets = cls._bullet_texts(entry)
            rows.append({
                'role': role,
                'master_bullets': master_bullets,
                'tailored_bullets': tailored_bullets,
                'changed': master_bullets != tailored_bullets,
                'reordered': cls._experience_order(master_experience) != cls._experience_order(tailored_experience),
            })
        return rows

    @classmethod
    def _bullet_texts(cls, entry: Dict[str, Any]) -> List[str]:
        texts = []
        for bullet in entry.get('bullets', []):
            if isinstance(bullet, dict):
                texts.append(bullet.get('text', ''))
            else:
                texts.append(str(bullet))
        return texts

    @classmethod
    def _experience_order(cls, experience: List[Dict[str, Any]]) -> List[str]:
        return [entry.get('id') or cls._role_label(entry) for entry in experience]

    @classmethod
    def _role_label(cls, entry: Dict[str, Any]) -> str:
        title = (entry.get('title') or 'Role').strip()
        company = (entry.get('company') or '').strip()
        return f'{title} @ {company}' if company else title


tailoring_diff_service = TailoringDiffService()
