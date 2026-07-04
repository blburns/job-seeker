"""LLM service with provider abstraction and structured JSON outputs."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """OpenAI-compatible LLM wrapper with heuristic fallback."""

    @classmethod
    def is_configured(cls) -> bool:
        return bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))

    @classmethod
    def _openai_chat(cls, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        import requests
        api_key = os.getenv('OPENAI_API_KEY', '')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY not configured')
        model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        body: Dict[str, Any] = {'model': model, 'messages': messages, 'temperature': 0.2}
        if json_mode:
            body['response_format'] = {'type': 'json_object'}
        resp = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    @classmethod
    def rephrase_bullet(cls, bullet_text: str, keyword: str, job_title: str = '') -> str:
        if not cls.is_configured():
            if keyword.lower() in bullet_text.lower():
                return bullet_text
            return f"{bullet_text.rstrip('.')}, including {keyword}." if bullet_text else bullet_text

        prompt = (
            f'Rephrase this resume bullet to naturally include the keyword "{keyword}" '
            f'for a {job_title} role. Do NOT invent new facts, metrics, or experience. '
            f'Return only the rephrased bullet text.\n\nBullet: {bullet_text}'
        )
        try:
            return cls._openai_chat([{'role': 'user', 'content': prompt}]).strip()
        except Exception as exc:
            logger.warning('LLM rephrase failed: %s', exc)
            return bullet_text

    @classmethod
    def generate_cover_letter(
        cls,
        profile_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
    ) -> str:
        contact = profile_data.get('contact', {})
        name = contact.get('name', 'Applicant')
        if not cls.is_configured():
            return (
                f'Dear Hiring Manager,\n\n'
                f'I am writing to express my interest in the {job_title} position at {company}. '
                f'My background aligns well with your requirements.\n\n'
                f'Sincerely,\n{name}'
            )
        prompt = (
            f'Write a concise professional cover letter (3 short paragraphs) for {name} '
            f'applying to {job_title} at {company}. Use only facts from this profile: '
            f'{json.dumps(profile_data)[:4000]}. Job description excerpt: {job_description[:2000]}'
        )
        try:
            return cls._openai_chat([{'role': 'user', 'content': prompt}])
        except Exception as exc:
            logger.warning('LLM cover letter failed: %s', exc)
            return ''

    @classmethod
    def extract_salary(cls, description: str) -> Dict[str, Optional[float]]:
        result = {'salary_min': None, 'salary_max': None}
        match = re.search(r'\$[\d,]+(?:k)?\s*[-–to]+\s*\$[\d,]+(?:k)?', description, re.I)
        if not match:
            return result
        nums = re.findall(r'[\d,]+', match.group())
        if len(nums) >= 2:
            result['salary_min'] = float(nums[0].replace(',', ''))
            result['salary_max'] = float(nums[1].replace(',', ''))
        return result

    @classmethod
    def gap_coaching(cls, missing_keywords: List[str], profile_data: Dict[str, Any]) -> List[str]:
        if not missing_keywords:
            return []
        if not cls.is_configured():
            return [f'Consider highlighting experience with {kw}' for kw in missing_keywords[:5]]
        prompt = (
            f'Given missing JD keywords {missing_keywords[:10]} and this resume JSON, '
            f'suggest 3 coaching tips (do not invent experience). Return JSON: {{"tips": []}}'
        )
        try:
            raw = cls._openai_chat(
                [{'role': 'user', 'content': prompt + json.dumps(profile_data)[:3000]}],
                json_mode=True,
            )
            return json.loads(raw).get('tips', [])
        except Exception:
            return [f'Consider highlighting experience with {kw}' for kw in missing_keywords[:5]]


llm_service = LLMService()
