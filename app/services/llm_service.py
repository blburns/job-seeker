"""LLM service with OpenAI + Google AI Studio (Gemini) providers and heuristic fallback."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMService:
    """Multi-provider LLM wrapper (OpenAI, Gemini) with heuristic fallback."""

    @classmethod
    def provider(cls) -> Optional[str]:
        """Return active provider name: 'openai', 'gemini', or None."""
        forced = (os.getenv('LLM_PROVIDER') or '').strip().lower()
        has_openai = bool(os.getenv('OPENAI_API_KEY', '').strip())
        has_gemini = bool(
            os.getenv('GEMINI_API_KEY', '').strip()
            or os.getenv('GOOGLE_API_KEY', '').strip()
        )
        if forced in ('openai', 'gemini'):
            if forced == 'openai' and has_openai:
                return 'openai'
            if forced == 'gemini' and has_gemini:
                return 'gemini'
            return None
        # auto: prefer Gemini when configured, else OpenAI
        if has_gemini:
            return 'gemini'
        if has_openai:
            return 'openai'
        return None

    @classmethod
    def is_configured(cls) -> bool:
        return cls.provider() is not None

    @classmethod
    def using_heuristic_fallback(cls) -> bool:
        return not cls.is_configured()

    @classmethod
    def _gemini_api_key(cls) -> str:
        return (
            os.getenv('GEMINI_API_KEY', '').strip()
            or os.getenv('GOOGLE_API_KEY', '').strip()
        )

    @classmethod
    def _chat(cls, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        provider = cls.provider()
        if provider == 'gemini':
            return cls._gemini_chat(messages, json_mode=json_mode)
        if provider == 'openai':
            return cls._openai_chat(messages, json_mode=json_mode)
        raise RuntimeError('No LLM provider configured')

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
    def _gemini_chat(cls, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Call Google AI Studio Generative Language API (Gemini)."""
        import requests

        api_key = cls._gemini_api_key()
        if not api_key:
            raise RuntimeError('GEMINI_API_KEY / GOOGLE_API_KEY not configured')

        model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        # Convert OpenAI-style messages to Gemini contents.
        # System messages are folded into the first user turn.
        system_bits: List[str] = []
        contents: List[Dict[str, Any]] = []
        for msg in messages:
            role = (msg.get('role') or 'user').lower()
            text = msg.get('content') or ''
            if role == 'system':
                system_bits.append(text)
                continue
            gemini_role = 'model' if role == 'assistant' else 'user'
            if system_bits and gemini_role == 'user':
                text = '\n\n'.join(system_bits + [text])
                system_bits = []
            contents.append({'role': gemini_role, 'parts': [{'text': text}]})
        if system_bits and not contents:
            contents.append({'role': 'user', 'parts': [{'text': '\n\n'.join(system_bits)}]})

        body: Dict[str, Any] = {
            'contents': contents,
            'generationConfig': {'temperature': 0.2},
        }
        if json_mode:
            body['generationConfig']['responseMimeType'] = 'application/json'

        url = (
            f'https://generativelanguage.googleapis.com/v1beta/models/'
            f'{model}:generateContent'
        )
        resp = requests.post(
            url,
            params={'key': api_key},
            headers={'Content-Type': 'application/json'},
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            parts = data['candidates'][0]['content']['parts']
            return ''.join(part.get('text', '') for part in parts).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f'Unexpected Gemini response: {data}') from exc

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
            return cls._chat([{'role': 'user', 'content': prompt}]).strip()
        except Exception as exc:
            logger.warning('LLM rephrase failed (%s): %s', cls.provider(), exc)
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
            return cls._chat([{'role': 'user', 'content': prompt}])
        except Exception as exc:
            logger.warning('LLM cover letter failed (%s): %s', cls.provider(), exc)
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
            raw = cls._chat(
                [{'role': 'user', 'content': prompt + json.dumps(profile_data)[:3000]}],
                json_mode=True,
            )
            return json.loads(raw).get('tips', [])
        except Exception:
            return [f'Consider highlighting experience with {kw}' for kw in missing_keywords[:5]]


llm_service = LLMService()
