"""Build and parse master profile data from manual ATS-style forms."""

import uuid
from typing import Any, Dict, List, Optional

from werkzeug.datastructures import ImmutableMultiDict


def _csv_list(value: str) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace('\n', ',').split(',') if part.strip()]


def _lines(value: str) -> List[str]:
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


class ProfileFormService:
    """Convert between HTML form posts and master profile JSON."""

    @classmethod
    def empty_form_context(cls) -> Dict[str, Any]:
        return {
            'contact': {
                'name': '', 'email': '', 'phone': '', 'location': '',
                'linkedin': '', 'website': '',
            },
            'headline': '',
            'summary': '',
            'application_defaults': {
                'work_authorization': '',
                'salary_expectation': '',
                'willing_to_relocate': '',
                'requires_sponsorship': '',
                'how_did_you_hear': 'Job board',
            },
            'skills': {'technical': '', 'soft': '', 'certifications': ''},
            'approved_keywords': '',
            'experience': [cls._empty_experience_row()],
            'education': [cls._empty_education_row()],
            'projects': [],
        }

    @classmethod
    def _empty_experience_row(cls) -> Dict[str, str]:
        return {
            'title': '', 'company': '', 'start': '', 'end': '',
            'location': '', 'bullets': '',
        }

    @classmethod
    def _empty_education_row(cls) -> Dict[str, str]:
        return {
            'institution': '', 'degree': '', 'field': '',
            'start': '', 'end': '', 'gpa': '',
        }

    @classmethod
    def _empty_project_row(cls) -> Dict[str, str]:
        return {'name': '', 'url': '', 'description': ''}

    @classmethod
    def profile_to_form_context(cls, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        contact = profile_data.get('contact', {})
        skills = profile_data.get('skills', {})
        defaults = profile_data.get('application_defaults', {})
        summary_variants = profile_data.get('summary_variants') or []
        summary = profile_data.get('summary') or ''
        if not summary and summary_variants:
            first = summary_variants[0]
            summary = first.get('text', '') if isinstance(first, dict) else str(first)

        experience = []
        for exp in profile_data.get('experience') or []:
            bullets = exp.get('bullets') or []
            bullet_lines = []
            for bullet in bullets:
                if isinstance(bullet, dict):
                    bullet_lines.append(bullet.get('text', ''))
                else:
                    bullet_lines.append(str(bullet))
            experience.append({
                'title': exp.get('title', ''),
                'company': exp.get('company', ''),
                'start': exp.get('start', ''),
                'end': exp.get('end', ''),
                'location': exp.get('location', ''),
                'bullets': '\n'.join(bullet_lines),
            })
        if not experience:
            experience = [cls._empty_experience_row()]

        education = []
        for edu in profile_data.get('education') or []:
            education.append({
                'institution': edu.get('institution', ''),
                'degree': edu.get('degree', ''),
                'field': edu.get('field', ''),
                'start': edu.get('start', ''),
                'end': edu.get('end', ''),
                'gpa': edu.get('gpa', ''),
            })
        if not education:
            education = [cls._empty_education_row()]

        projects = []
        for proj in profile_data.get('projects') or []:
            projects.append({
                'name': proj.get('name', ''),
                'url': proj.get('url', ''),
                'description': proj.get('description', ''),
            })

        return {
            'contact': {
                'name': contact.get('name', ''),
                'email': contact.get('email', ''),
                'phone': contact.get('phone', ''),
                'location': contact.get('location', ''),
                'linkedin': contact.get('linkedin', ''),
                'website': contact.get('website', ''),
            },
            'headline': profile_data.get('headline', ''),
            'summary': summary,
            'application_defaults': {
                'work_authorization': defaults.get('work_authorization', ''),
                'salary_expectation': defaults.get('salary_expectation', ''),
                'willing_to_relocate': defaults.get('willing_to_relocate', ''),
                'requires_sponsorship': defaults.get('requires_sponsorship', ''),
                'how_did_you_hear': defaults.get('how_did_you_hear', 'Job board'),
            },
            'skills': {
                'technical': ', '.join(skills.get('technical') or []),
                'soft': ', '.join(skills.get('soft') or []),
                'certifications': ', '.join(skills.get('certifications') or []),
            },
            'approved_keywords': ', '.join(profile_data.get('approved_keywords') or []),
            'experience': experience,
            'education': education,
            'projects': projects,
        }

    @classmethod
    def build_profile_from_form(
        cls,
        form: ImmutableMultiDict,
        existing: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from app.services.resume_parser_service import resume_parser_service

        existing = existing or {}
        existing_exp = existing.get('experience') or []

        experience = []
        titles = form.getlist('exp_title[]')
        for idx, title in enumerate(titles):
            company = form.getlist('exp_company[]')[idx] if idx < len(form.getlist('exp_company[]')) else ''
            if not any([
                title.strip(), company.strip(),
                (form.getlist('exp_bullets[]')[idx] if idx < len(form.getlist('exp_bullets[]')) else '').strip(),
            ]):
                continue
            bullets_raw = form.getlist('exp_bullets[]')[idx] if idx < len(form.getlist('exp_bullets[]')) else ''
            prior_exp = existing_exp[idx] if idx < len(existing_exp) else {}
            prior_bullets = prior_exp.get('bullets') or []
            bullets = []
            for b_idx, line in enumerate(_lines(bullets_raw)):
                bullet_id = None
                if b_idx < len(prior_bullets) and isinstance(prior_bullets[b_idx], dict):
                    bullet_id = prior_bullets[b_idx].get('id')
                bullet = resume_parser_service.make_bullet(line)
                if bullet_id:
                    bullet['id'] = bullet_id
                bullets.append(bullet)
            experience.append({
                'id': prior_exp.get('id') or str(uuid.uuid4()),
                'title': title.strip(),
                'company': company.strip(),
                'start': (form.getlist('exp_start[]')[idx] if idx < len(form.getlist('exp_start[]')) else '').strip(),
                'end': (form.getlist('exp_end[]')[idx] if idx < len(form.getlist('exp_end[]')) else '').strip(),
                'location': (form.getlist('exp_location[]')[idx] if idx < len(form.getlist('exp_location[]')) else '').strip(),
                'bullets': bullets,
            })

        existing_edu = existing.get('education') or []
        education = []
        institutions = form.getlist('edu_institution[]')
        for idx, institution in enumerate(institutions):
            degree = form.getlist('edu_degree[]')[idx] if idx < len(form.getlist('edu_degree[]')) else ''
            if not institution.strip() and not degree.strip():
                continue
            prior_edu = existing_edu[idx] if idx < len(existing_edu) else {}
            education.append({
                'id': prior_edu.get('id') or str(uuid.uuid4()),
                'institution': institution.strip(),
                'degree': degree.strip(),
                'field': (form.getlist('edu_field[]')[idx] if idx < len(form.getlist('edu_field[]')) else '').strip(),
                'start': (form.getlist('edu_start[]')[idx] if idx < len(form.getlist('edu_start[]')) else '').strip(),
                'end': (form.getlist('edu_end[]')[idx] if idx < len(form.getlist('edu_end[]')) else '').strip(),
                'gpa': (form.getlist('edu_gpa[]')[idx] if idx < len(form.getlist('edu_gpa[]')) else '').strip(),
            })

        existing_proj = existing.get('projects') or []
        projects = []
        names = form.getlist('proj_name[]')
        for idx, name in enumerate(names):
            if not name.strip():
                continue
            prior = existing_proj[idx] if idx < len(existing_proj) else {}
            projects.append({
                'id': prior.get('id') or str(uuid.uuid4()),
                'name': name.strip(),
                'url': (form.getlist('proj_url[]')[idx] if idx < len(form.getlist('proj_url[]')) else '').strip(),
                'description': (form.getlist('proj_description[]')[idx] if idx < len(form.getlist('proj_description[]')) else '').strip(),
                'skills': [],
            })

        summary = form.get('summary', '').strip()
        existing_variants = existing.get('summary_variants') or []
        prior_variant = existing_variants[0] if existing_variants else {}
        if summary:
            summary_variants = [{
                'id': (prior_variant.get('id') if isinstance(prior_variant, dict) else None) or str(uuid.uuid4()),
                'text': summary,
                'tags': prior_variant.get('tags', []) if isinstance(prior_variant, dict) else [],
            }]
        else:
            summary_variants = []
        profile = {
            'contact': {
                'name': form.get('contact_name', '').strip(),
                'email': form.get('contact_email', '').strip(),
                'phone': form.get('contact_phone', '').strip(),
                'location': form.get('contact_location', '').strip(),
                'linkedin': form.get('contact_linkedin', '').strip(),
                'website': form.get('contact_website', '').strip(),
            },
            'headline': form.get('headline', '').strip(),
            'summary_variants': summary_variants,
            'summary': summary,
            'application_defaults': {
                'work_authorization': form.get('work_authorization', '').strip(),
                'salary_expectation': form.get('salary_expectation', '').strip(),
                'willing_to_relocate': form.get('willing_to_relocate', '').strip(),
                'requires_sponsorship': form.get('requires_sponsorship', '').strip(),
                'how_did_you_hear': form.get('how_did_you_hear', '').strip() or 'Job board',
            },
            'experience': experience,
            'education': education,
            'skills': {
                'technical': _csv_list(form.get('skills_technical', '')),
                'soft': _csv_list(form.get('skills_soft', '')),
                'certifications': _csv_list(form.get('skills_certifications', '')),
            },
            'approved_keywords': _csv_list(form.get('approved_keywords', '')),
            'projects': projects,
        }
        return profile


profile_form_service = ProfileFormService()
