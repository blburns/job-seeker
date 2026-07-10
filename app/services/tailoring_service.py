"""
Tailoring Service
Constrained resume tailoring with diff audit trail.
"""

import copy
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.keyword_service import keyword_service
from app.services.llm_service import llm_service


class TailoringService:
    """Tailor master profile for a job posting without inventing facts."""

    MAX_BULLET_CHANGES = 5

    @classmethod
    def tailor_for_job(
        cls,
        master_data: Dict[str, Any],
        job_title: str,
        job_description: str,
        company: str = '',
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        tailored = copy.deepcopy(master_data)
        diff_log: List[Dict[str, Any]] = []

        tailored['headline'] = job_title or tailored.get('headline', '')
        diff_log.append({
            'field': 'headline',
            'action': 'set',
            'old': master_data.get('headline'),
            'new': tailored['headline'],
            'master_ref': None,
        })

        if company:
            tailored['_target_company'] = company

        analysis = keyword_service.analyze_coverage(job_description, master_data)
        missing = analysis.get('missing_keywords', [])
        jd_keywords = set(analysis.get('jd_keywords', []))

        summary = cls._select_summary(tailored, jd_keywords)
        if summary:
            old_summary = cls._primary_summary(master_data)
            diff_log.append({
                'field': 'summary',
                'action': 'select_variant',
                'master_ref': summary.get('id'),
                'old': old_summary,
                'new': summary.get('text'),
            })
            tailored['summary_variants'] = [summary]

        reordered_exp, exp_diffs = cls._reorder_experience(tailored.get('experience', []), jd_keywords)
        tailored['experience'] = reordered_exp
        diff_log.extend(exp_diffs)

        reordered_skills, skill_diff = cls._reorder_skills(tailored.get('skills', {}), jd_keywords)
        tailored['skills'] = reordered_skills
        if skill_diff:
            diff_log.append(skill_diff)

        bullet_diffs = cls._rephrase_bullets(
            tailored,
            cls.filter_insertable_keywords(missing, master_data)[:cls.MAX_BULLET_CHANGES],
        )
        diff_log.extend(bullet_diffs)

        return tailored, diff_log

    @classmethod
    def approved_keyword_set(cls, profile_data: Dict[str, Any]) -> set:
        """Normalized allowlist of keywords the user authorizes for bullet inserts."""
        return {
            str(kw).strip().lower()
            for kw in (profile_data.get('approved_keywords') or [])
            if str(kw).strip()
        }

    @classmethod
    def filter_insertable_keywords(
        cls,
        missing_keywords: List[str],
        profile_data: Dict[str, Any],
    ) -> List[str]:
        """
        Only JD keywords the user approved may be woven into bullets.

        Empty approved_keywords → no inserts (avoids inventing claims).
        """
        allow = cls.approved_keyword_set(profile_data)
        if not allow:
            return []
        insertable = []
        for kw in missing_keywords:
            lower = (kw or '').strip().lower()
            if not lower:
                continue
            if lower in allow or any(
                lower in approved or approved in lower for approved in allow
            ):
                insertable.append(kw)
        return insertable

    @classmethod
    def _role_label(cls, entry: Dict[str, Any]) -> str:
        title = (entry.get('title') or 'Role').strip()
        company = (entry.get('company') or '').strip()
        return f'{title} @ {company}' if company else title

    @classmethod
    def _experience_labels(cls, experience: List[Dict[str, Any]], ids: List[Any]) -> List[str]:
        lookup = {
            entry.get('id'): cls._role_label(entry)
            for entry in experience
            if entry.get('id')
        }
        return [lookup.get(entry_id, str(entry_id)) for entry_id in ids]

    @classmethod
    def _primary_summary(cls, profile: Dict[str, Any]) -> str:
        variants = profile.get('summary_variants') or []
        if variants:
            first = cls._normalize_summary_variant(variants[0])
            return first.get('text', '')
        return profile.get('summary', '') or ''

    @classmethod
    def _normalize_summary_variant(cls, variant: Any) -> Dict[str, Any]:
        if isinstance(variant, dict):
            return variant
        text = str(variant).strip()
        if not text:
            return {}
        return {'id': None, 'text': text, 'tags': []}

    @classmethod
    def _select_summary(cls, profile: Dict[str, Any], jd_keywords: set) -> Optional[Dict[str, Any]]:
        variants = profile.get('summary_variants', [])
        if not variants:
            return None
        best = cls._normalize_summary_variant(variants[0])
        best_score = 0
        for variant in variants:
            variant = cls._normalize_summary_variant(variant)
            if not variant:
                continue
            text = variant.get('text', '').lower()
            score = sum(1 for kw in jd_keywords if kw in text)
            tags = variant.get('tags', [])
            score += sum(1 for tag in tags if tag.lower() in jd_keywords)
            if score > best_score:
                best_score = score
                best = variant
        return best or None

    @classmethod
    def _reorder_experience(cls, experience: List[Dict[str, Any]], jd_keywords: set) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if not experience:
            return [], []

        def relevance_score(entry: Dict[str, Any]) -> int:
            text = ' '.join([
                entry.get('title', ''),
                entry.get('company', ''),
                ' '.join(
                    b.get('text', '') if isinstance(b, dict) else str(b)
                    for b in entry.get('bullets', [])
                ),
            ]).lower()
            return sum(1 for kw in jd_keywords if kw in text)

        scored = sorted(experience, key=relevance_score, reverse=True)
        old_order = [e.get('id') for e in experience]
        new_order = [e.get('id') for e in scored]
        diffs = []
        if old_order != new_order:
            diffs.append({
                'field': 'experience',
                'action': 'reorder',
                'old_order': old_order,
                'new_order': new_order,
                'old_labels': cls._experience_labels(experience, old_order),
                'new_labels': cls._experience_labels(scored, new_order),
                'master_ref': None,
            })
        return scored, diffs

    @classmethod
    def _reorder_skills(cls, skills: Dict[str, Any], jd_keywords: set) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        if not isinstance(skills, dict):
            return {'technical': [], 'certifications': []}, None
        technical = list(skills.get('technical', []))

        def skill_priority(skill: str) -> int:
            lower = skill.lower()
            for i, kw in enumerate(jd_keywords):
                if kw in lower or lower in kw:
                    return i
            return 999

        reordered = sorted(technical, key=skill_priority)
        if reordered != technical:
            return {
                'technical': reordered,
                'certifications': skills.get('certifications', []),
            }, {
                'field': 'skills.technical',
                'action': 'reorder',
                'old': technical,
                'new': reordered,
                'master_ref': None,
            }
        return skills, None

    @classmethod
    def _rephrase_bullets(cls, profile: Dict[str, Any], missing_keywords: List[str]) -> List[Dict[str, Any]]:
        diffs = []
        if not missing_keywords:
            return diffs

        keyword_idx = 0
        for entry in profile.get('experience', []):
            for bullet in entry.get('bullets', []):
                if keyword_idx >= len(missing_keywords):
                    break
                if not isinstance(bullet, dict):
                    continue
                kw = missing_keywords[keyword_idx]
                old_text = bullet.get('text', '')
                if kw.lower() in old_text.lower():
                    keyword_idx += 1
                    continue
                new_text = cls._natural_rephrase(
                    old_text, kw, profile.get('headline', '')
                )
                if new_text != old_text:
                    diffs.append({
                        'field': 'experience.bullet',
                        'action': 'rephrase',
                        'master_ref': bullet.get('id'),
                        'role': cls._role_label(entry),
                        'old': old_text,
                        'new': new_text,
                        'keyword_added': kw,
                    })
                    bullet['text'] = new_text
                    keyword_idx += 1
        return diffs

    @classmethod
    def _natural_rephrase(cls, text: str, keyword: str, job_title: str = '') -> str:
        """Add keyword naturally if not already present. No new facts."""
        if keyword.lower() in text.lower():
            return text
        return llm_service.rephrase_bullet(text, keyword, job_title)

    @classmethod
    def tailor_for_job_with_coverage(
        cls,
        master_data: Dict[str, Any],
        job_title: str,
        job_description: str,
        company: str = '',
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], float]:
        analysis_before = keyword_service.analyze_coverage(job_description, master_data)
        tailored, diff_log = cls.tailor_for_job(master_data, job_title, job_description, company)
        analysis_after = keyword_service.analyze_coverage(job_description, tailored)
        diff_log.append({
            '_meta': True,
            'field': '_meta',
            'action': 'summary',
            'coverage_before': analysis_before.get('coverage_score', 0),
            'coverage_after': analysis_after.get('coverage_score', 0),
            'matched_before': analysis_before.get('matched_keywords', []),
            'matched_after': analysis_after.get('matched_keywords', []),
            'missing_after': analysis_after.get('missing_keywords', []),
            'jd_keywords': analysis_after.get('jd_keywords', []),
        })
        return tailored, diff_log, float(analysis_after.get('coverage_score', 0))

    @classmethod
    def generate_cover_letter_for_job(
        cls,
        master_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
    ) -> str:
        return llm_service.generate_cover_letter(master_data, job_title, company, job_description)

    @classmethod
    def reject_change(
        cls,
        tailored_data: Dict[str, Any],
        diff_log: List[Dict[str, Any]],
        change_index: int,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Revert one diff entry in tailored_data and mark it rejected in the log."""
        if change_index < 0 or change_index >= len(diff_log):
            raise ValueError('Invalid change index')

        change = diff_log[change_index]
        if change.get('_meta') or change.get('field') == '_meta':
            raise ValueError('Cannot reject metadata entries')
        if change.get('rejected'):
            raise ValueError('Change already rejected')

        tailored = copy.deepcopy(tailored_data)
        action = change.get('action')
        field = change.get('field')

        if action == 'rephrase' and field == 'experience.bullet':
            cls._restore_bullet(tailored, change)
        elif action == 'set' and field == 'headline':
            tailored['headline'] = change.get('old') or ''
        elif action == 'select_variant' and field == 'summary':
            old_text = change.get('old') or ''
            if old_text:
                tailored['summary_variants'] = [{
                    'id': change.get('master_ref'),
                    'text': old_text,
                    'tags': [],
                }]
                tailored['summary'] = old_text
        elif action == 'reorder' and field == 'experience':
            cls._restore_experience_order(tailored, change.get('old_order') or [])
        elif action == 'reorder' and field == 'skills.technical':
            skills = tailored.get('skills') or {}
            if not isinstance(skills, dict):
                skills = {'technical': [], 'certifications': []}
            skills['technical'] = list(change.get('old') or [])
            tailored['skills'] = skills
        else:
            raise ValueError(f"Cannot reject change type: {action}/{field}")

        updated_log = list(diff_log)
        updated_change = dict(change)
        updated_change['rejected'] = True
        updated_log[change_index] = updated_change
        return tailored, updated_log

    @classmethod
    def _restore_bullet(cls, tailored: Dict[str, Any], change: Dict[str, Any]) -> None:
        bullet_id = change.get('master_ref')
        old_text = change.get('old')
        new_text = change.get('new')
        for entry in tailored.get('experience', []):
            for bullet in entry.get('bullets', []):
                if not isinstance(bullet, dict):
                    continue
                if bullet_id and bullet.get('id') == bullet_id:
                    bullet['text'] = old_text if old_text is not None else bullet.get('text', '')
                    return
                if new_text is not None and bullet.get('text') == new_text:
                    bullet['text'] = old_text if old_text is not None else bullet.get('text', '')
                    return
        raise ValueError('Could not find bullet to restore')

    @classmethod
    def _restore_experience_order(cls, tailored: Dict[str, Any], old_order: List[Any]) -> None:
        experience = tailored.get('experience') or []
        if not old_order or not experience:
            return
        by_id = {entry.get('id'): entry for entry in experience if entry.get('id')}
        restored = [by_id[entry_id] for entry_id in old_order if entry_id in by_id]
        # Keep any entries missing from old_order at the end
        seen = set(old_order)
        restored.extend(entry for entry in experience if entry.get('id') not in seen)
        tailored['experience'] = restored

    @classmethod
    def validate_diff(cls, diff_log: List[Dict[str, Any]], master_data: Dict[str, Any]) -> List[str]:
        """Ensure all changes reference valid master profile IDs."""
        errors = []
        master_bullet_ids = set()
        for exp in master_data.get('experience', []):
            for bullet in exp.get('bullets', []):
                if isinstance(bullet, dict) and bullet.get('id'):
                    master_bullet_ids.add(bullet['id'])

        for change in diff_log:
            if change.get('rejected'):
                continue
            ref = change.get('master_ref')
            if change.get('field') == 'experience.bullet' and ref and ref not in master_bullet_ids:
                errors.append(f"Orphan bullet reference: {ref}")
        return errors

    @classmethod
    def approve_version(cls, version_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **version_data,
            'status': 'approved',
            'approved_at': datetime.utcnow().isoformat(),
        }


tailoring_service = TailoringService()
