"""
Keyword Service
Extracts keywords from job descriptions and analyzes coverage against master profile.
"""

import re
from typing import Any, Dict, List, Set, Tuple


class KeywordService:
    """JD keyword extraction and resume gap analysis."""

    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'shall', 'can', 'need', 'our', 'your', 'we', 'you', 'they', 'their', 'this', 'that',
        'these', 'those', 'it', 'its', 'who', 'what', 'which', 'when', 'where', 'how', 'all',
        'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'about', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'any', 'both', 'work', 'working', 'role',
        'position', 'job', 'team', 'company', 'ability', 'experience', 'years', 'year',
        'including', 'required', 'preferred', 'responsibilities', 'qualifications',
    }

    SYNONYMS = {
        'javascript': ['js', 'ecmascript'],
        'typescript': ['ts'],
        'python': ['py'],
        'postgresql': ['postgres', 'psql'],
        'kubernetes': ['k8s'],
        'amazon web services': ['aws'],
        'machine learning': ['ml'],
        'artificial intelligence': ['ai'],
        'continuous integration': ['ci'],
        'continuous delivery': ['cd'],
        'applicant tracking system': ['ats'],
    }

    TECH_PATTERNS = [
        r'\b(?:python|java|javascript|typescript|ruby|go|golang|rust|c\+\+|c#|php|swift|kotlin)\b',
        r'\b(?:react|angular|vue|node\.?js|django|flask|fastapi|spring|rails)\b',
        r'\b(?:postgresql|mysql|mongodb|redis|elasticsearch|dynamodb|sqlite)\b',
        r'\b(?:aws|azure|gcp|docker|kubernetes|terraform|ansible)\b',
        r'\b(?:git|jenkins|github|gitlab|ci/?cd|agile|scrum|jira)\b',
        r'\b(?:rest|graphql|api|microservices|sql|nosql)\b',
        r'\b(?:machine learning|deep learning|nlp|data science|etl)\b',
    ]

    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        if not text:
            return []
        keywords: Set[str] = set()
        lower = text.lower()

        for pattern in cls.TECH_PATTERNS:
            for match in re.finditer(pattern, lower, re.I):
                keywords.add(match.group(0).lower())

        words = re.findall(r'\b[a-z][a-z0-9+#./-]{1,30}\b', lower)
        for word in words:
            if word not in cls.STOP_WORDS and len(word) > 2:
                if word in keywords or len(word) >= 4:
                    keywords.add(word)

        return sorted(keywords)[:100]

    @classmethod
    def profile_to_text(cls, profile_data: Dict[str, Any]) -> str:
        parts = []
        parts.append(profile_data.get('headline', ''))
        for variant in profile_data.get('summary_variants', []):
            if isinstance(variant, dict):
                parts.append(variant.get('text', ''))
            else:
                parts.append(str(variant))
        for exp in profile_data.get('experience', []):
            parts.append(exp.get('title', ''))
            parts.append(exp.get('company', ''))
            for bullet in exp.get('bullets', []):
                parts.append(bullet.get('text', '') if isinstance(bullet, dict) else str(bullet))
        skills = profile_data.get('skills', {})
        if isinstance(skills, dict):
            parts.extend(skills.get('technical', []))
            parts.extend(skills.get('certifications', []))
        for edu in profile_data.get('education', []):
            parts.append(edu.get('institution', ''))
            parts.append(edu.get('degree', ''))
        return ' '.join(parts).lower()

    @classmethod
    def analyze_coverage(cls, jd_text: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        jd_keywords = cls.extract_keywords(jd_text)
        profile_text = cls.profile_to_text(profile_data)

        matched = []
        missing = []
        synonym_matches = []

        for keyword in jd_keywords:
            if keyword in profile_text:
                matched.append(keyword)
            elif cls._synonym_match(keyword, profile_text):
                synonym_matches.append({'keyword': keyword, 'matched_via': 'synonym'})
            else:
                missing.append(keyword)

        total = len(jd_keywords) or 1
        coverage = round((len(matched) + len(synonym_matches) * 0.5) / total * 100, 1)

        return {
            'jd_keywords': jd_keywords,
            'matched_keywords': matched,
            'missing_keywords': missing,
            'synonym_matches': synonym_matches,
            'coverage_score': min(coverage, 100.0),
        }

    @classmethod
    def _synonym_match(cls, keyword: str, profile_text: str) -> bool:
        for canonical, synonyms in cls.SYNONYMS.items():
            terms = [canonical] + synonyms
            if keyword in terms:
                return any(term in profile_text for term in terms)
        return False

    @classmethod
    def highlight_keywords(cls, text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        results = []
        lower = text.lower()
        for kw in keywords:
            status = 'matched' if kw in lower else 'missing'
            results.append({'keyword': kw, 'status': status})
        return results


keyword_service = KeywordService()
