"""
Keyword Service
Extracts keywords from job descriptions and analyzes coverage against master profile.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


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
        # Common JD fluff
        'candidate', 'candidates', 'applicant', 'applicants', 'looking', 'seeking',
        'opportunity', 'opportunities', 'join', 'help', 'ensure', 'strong', 'excellent',
        'good', 'great', 'solid', 'proven', 'track', 'record', 'passionate', 'excited',
        'collaborative', 'environment', 'culture', 'benefits', 'compensation', 'salary',
        'equal', 'opportunity', 'employer', 'status', 'gender', 'race', 'disability',
        'please', 'apply', 'submit', 'resume', 'cover', 'letter', 'description',
        'overview', 'about', 'us', 'mission', 'vision', 'values', 'etc',
        'minimum', 'plus', 'bonus', 'nice', 'have', 'must', 'using', 'use', 'used',
        'across', 'within', 'based', 'related', 'various', 'multiple', 'well',
    }

    HIGH_SIGNAL_HEADERS = (
        'requirements', 'qualifications', 'skills', 'technical skills',
        'required skills', 'preferred skills', 'must have', 'nice to have',
        'what you will need', "what you'll need", 'you have', 'you bring',
        'minimum qualifications', 'preferred qualifications', 'basic qualifications',
        'tech stack', 'technologies', 'tools', 'expertise',
    )

    LOW_SIGNAL_HEADERS = (
        'responsibilities', 'about the role', 'about us', 'the role',
        'what you will do', "what you'll do", 'benefits', 'perks',
        'compensation', 'equal opportunity', 'how to apply',
    )

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
        'node.js': ['nodejs', 'node'],
        'ci/cd': ['cicd', 'ci-cd'],
    }

    TECH_PATTERNS = [
        r'\b(?:python|java|javascript|typescript|ruby|go|golang|rust|c\+\+|c#|php|swift|kotlin)\b',
        r'\b(?:react|angular|vue|node\.?js|django|flask|fastapi|spring|rails)\b',
        r'\b(?:postgresql|mysql|mongodb|redis|elasticsearch|dynamodb|sqlite)\b',
        r'\b(?:aws|azure|gcp|docker|kubernetes|terraform|ansible)\b',
        r'\b(?:git|jenkins|github|gitlab|ci/?cd|agile|scrum|jira)\b',
        r'\b(?:rest|graphql|api|microservices|sql|nosql)\b',
        r'\b(?:machine learning|deep learning|nlp|data science|etl)\b',
        r'\b(?:linux|unix|bash|shell|pytest|unittest|selenium|playwright)\b',
        r'\b(?:kafka|rabbitmq|celery|redis|nginx|gunicorn)\b',
    ]

    BULLET_LINE = re.compile(r'^[\s]*[\u2022\u2023\u25E6\u2043\u25AA\u25CF\-\*•◦▪]\s*(.+)$')
    SECTION_HEADER = re.compile(
        r'^[\s#]*([A-Za-z][A-Za-z0-9 /&\'-]{2,60})\s*:?\s*$'
    )

    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        if not text:
            return []

        sections = cls._split_jd_sections(text)
        scored: Dict[str, float] = {}

        for section_name, section_text, weight in sections:
            for kw in cls._extract_from_chunk(section_text):
                scored[kw] = scored.get(kw, 0.0) + weight

            # Bullet lines in any section get a boost
            for line in section_text.splitlines():
                bullet = cls.BULLET_LINE.match(line)
                if not bullet:
                    continue
                for kw in cls._extract_from_chunk(bullet.group(1)):
                    scored[kw] = scored.get(kw, 0.0) + 0.5

        # Prefer higher scores, then alphabetical for stability
        ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0]))
        return [kw for kw, _ in ranked[:100]]

    @classmethod
    def _split_jd_sections(cls, text: str) -> List[Tuple[str, str, float]]:
        """Split JD into named sections with signal weights."""
        lines = text.replace('\r\n', '\n').split('\n')
        sections: List[Tuple[str, List[str], float]] = [('body', [], 1.0)]
        current_name = 'body'
        current_weight = 1.0
        current_lines: List[str] = sections[0][1]

        for raw in lines:
            line = raw.strip()
            header = cls._match_section_header(line)
            if header:
                if current_lines or current_name != 'body':
                    sections.append((current_name, current_lines, current_weight))
                current_name = header
                current_weight = cls._section_weight(header)
                current_lines = []
                continue
            current_lines.append(raw)

        sections.append((current_name, current_lines, current_weight))
        # Drop the placeholder empty body if we never used it
        result = []
        for name, chunk_lines, weight in sections:
            chunk = '\n'.join(chunk_lines).strip()
            if chunk:
                result.append((name, chunk, weight))
        return result or [('body', text, 1.0)]

    @classmethod
    def _match_section_header(cls, line: str) -> Optional[str]:
        if not line or len(line) > 70:
            return None
        cleaned = line.strip('#').strip().rstrip(':').strip().lower()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        known = cls.HIGH_SIGNAL_HEADERS + cls.LOW_SIGNAL_HEADERS
        if cleaned in known:
            return cleaned
        match = cls.SECTION_HEADER.match(line)
        if not match:
            return None
        candidate = match.group(1).strip().lower()
        if candidate in known:
            return candidate
        return None

    @classmethod
    def _section_weight(cls, header: str) -> float:
        if header in cls.HIGH_SIGNAL_HEADERS:
            return 2.5
        if header in cls.LOW_SIGNAL_HEADERS:
            return 0.6
        return 1.0

    @classmethod
    def _extract_from_chunk(cls, text: str) -> Set[str]:
        keywords: Set[str] = set()
        lower = text.lower()

        for pattern in cls.TECH_PATTERNS:
            for match in re.finditer(pattern, lower, re.I):
                keywords.add(match.group(0).lower())

        # Comma / pipe separated skill lists (common in Skills sections)
        for token in re.split(r'[,;/|•]', lower):
            token = token.strip()
            if 2 < len(token) <= 40 and ' ' not in token and token not in cls.STOP_WORDS:
                if re.fullmatch(r'[a-z][a-z0-9+#./-]{1,30}', token):
                    keywords.add(token)

        words = re.findall(r'\b[a-z][a-z0-9+#./-]{1,30}\b', lower)
        for word in words:
            if word in cls.STOP_WORDS or len(word) < 3:
                continue
            if word in keywords or len(word) >= 4:
                keywords.add(word)

        return keywords

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
