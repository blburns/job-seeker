"""
Job Discovery Service
Fetch and score job postings from URLs and external sources.
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from app.services.keyword_service import keyword_service


class JobDiscoveryService:
    """Discover and normalize job postings."""

    REQUEST_TIMEOUT = 15
    USER_AGENT = 'JobSeekerBot/1.0 (+https://localhost)'

    @classmethod
    def fetch_from_url(cls, url: str) -> Dict[str, Any]:
        response = requests.get(
            url,
            timeout=cls.REQUEST_TIMEOUT,
            headers={'User-Agent': cls.USER_AGENT},
        )
        response.raise_for_status()
        text = response.text
        return cls._parse_html_job(text, url)

    @classmethod
    def _parse_html_job(cls, html: str, url: str) -> Dict[str, Any]:
        title = cls._extract_meta(html, 'og:title') or cls._extract_title_tag(html) or 'Untitled Position'
        description = cls._extract_meta(html, 'og:description') or cls._extract_description(html)
        company = cls._guess_company(url, html)

        return {
            'title': cls._clean_text(title),
            'company': company,
            'description': description,
            'url': url,
            'source': 'url',
            'extracted_keywords': keyword_service.extract_keywords(description),
            'location': cls._extract_location(description),
            'seniority': cls._detect_seniority(title + ' ' + description),
        }

    @classmethod
    def _extract_meta(cls, html: str, property_name: str) -> Optional[str]:
        pattern = rf'<meta[^>]+property=["\']{property_name}["\'][^>]+content=["\']([^"\']+)["\']'
        match = re.search(pattern, html, re.I)
        if match:
            return match.group(1)
        pattern2 = rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{property_name}["\']'
        match = re.search(pattern2, html, re.I)
        return match.group(1) if match else None

    @classmethod
    def _extract_title_tag(cls, html: str) -> Optional[str]:
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        return match.group(1).strip() if match else None

    @classmethod
    def _extract_description(cls, html: str) -> str:
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.S | re.I)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:15000]

    @classmethod
    def _guess_company(cls, url: str, html: str) -> str:
        domain = urlparse(url).netloc.replace('www.', '')
        parts = domain.split('.')
        if parts:
            return parts[0].replace('-', ' ').title()
        return 'Unknown Company'

    @classmethod
    def _extract_location(cls, text: str) -> str:
        patterns = [
            r'(?:location|based in|office in)[:\s]+([A-Za-z\s,]+?)(?:\.|$|\n)',
            r'\b(Remote|Hybrid|On-site)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()[:100]
        return ''

    @classmethod
    def _detect_seniority(cls, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ['principal', 'staff', 'distinguished']):
            return 'principal'
        if any(w in lower for w in ['senior', 'sr.', 'sr ']):
            return 'senior'
        if any(w in lower for w in ['junior', 'jr.', 'entry level', 'graduate']):
            return 'junior'
        if 'mid' in lower or 'intermediate' in lower:
            return 'mid'
        return 'unspecified'

    @classmethod
    def calculate_fit_score(cls, job_keywords: List[str], profile_data: Dict[str, Any]) -> int:
        if not job_keywords:
            return 0
        profile_text = keyword_service.profile_to_text(profile_data)
        matched = sum(1 for kw in job_keywords if kw in profile_text)
        return min(100, round(matched / len(job_keywords) * 100))

    @classmethod
    def build_apply_draft(cls, profile_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        contact = profile_data.get('contact', {})
        experience = profile_data.get('experience', [])
        defaults = profile_data.get('application_defaults', {})
        return {
            'full_name': contact.get('name', ''),
            'email': contact.get('email', ''),
            'phone': contact.get('phone', ''),
            'location': contact.get('location', ''),
            'linkedin': contact.get('linkedin', ''),
            'website': contact.get('website', ''),
            'current_title': profile_data.get('headline', ''),
            'current_company': experience[0].get('company', '') if experience else '',
            'years_experience': str(len(experience) * 2),
            'work_authorization': defaults.get('work_authorization', ''),
            'salary_expectation': defaults.get('salary_expectation', ''),
            'willing_to_relocate': defaults.get('willing_to_relocate', ''),
            'requires_sponsorship': defaults.get('requires_sponsorship', ''),
            'cover_letter': '',
            'how_did_you_hear': defaults.get('how_did_you_hear', 'Job board'),
            'job_title': job_data.get('title', ''),
            'job_company': job_data.get('company', ''),
            'job_url': job_data.get('url', ''),
        }

    @classmethod
    def search_rss_feed(cls, feed_url: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Basic RSS job feed parser."""
        import xml.etree.ElementTree as ET
        response = requests.get(feed_url, timeout=cls.REQUEST_TIMEOUT, headers={'User-Agent': cls.USER_AGENT})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall('.//item')[:limit]:
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            description = item.findtext('description', '')
            items.append({
                'title': cls._clean_text(title),
                'company': '',
                'description': cls._clean_text(description),
                'url': link,
                'source': 'rss',
                'extracted_keywords': keyword_service.extract_keywords(description),
            })
        return items

    @classmethod
    def _clean_text(cls, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        return re.sub(r'\s+', ' ', text).strip()


job_discovery_service = JobDiscoveryService()
