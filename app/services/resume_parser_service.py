"""
Resume Parser Service
Extracts structured profile data from PDF/DOCX uploads.
"""

import io
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple


class ResumeParserService:
    """Parse resume files into structured master profile JSON."""

    SECTION_PATTERNS = {
        'summary': re.compile(r'^(summary|profile|objective|about)\s*$', re.I),
        'experience': re.compile(r'^(experience|work\s*history|employment)\s*$', re.I),
        'education': re.compile(r'^education\s*$', re.I),
        'skills': re.compile(r'^(skills|technical\s*skills|core\s*competencies)\s*$', re.I),
        'projects': re.compile(r'^projects?\s*$', re.I),
    }

    BULLET_PATTERN = re.compile(r'^[\u2022\u2023\u25E6\u2043\-\*•]\s*')
    DATE_PATTERN = re.compile(
        r'(\d{1,2}/\d{4}|\d{4}|\w+\s+\d{4})\s*[-–—]\s*(\d{1,2}/\d{4}|\d{4}|\w+\s+\d{4}|present|current)',
        re.I
    )
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    PHONE_PATTERN = re.compile(r'(\+?\d[\d\s().-]{7,}\d)')
    LINKEDIN_PATTERN = re.compile(r'linkedin\.com/in/[\w-]+', re.I)

    @classmethod
    def parse_file(cls, file_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], float]:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext == 'docx':
            text = cls._extract_docx(file_bytes)
        elif ext == 'pdf':
            text = cls._extract_pdf(file_bytes)
        elif ext in ('txt', 'text'):
            text = file_bytes.decode('utf-8', errors='replace')
        else:
            raise ValueError(f'Unsupported file type: {ext}. Use PDF, DOCX, or TXT.')

        profile = cls.parse_text(text)
        confidence = cls._estimate_confidence(profile)
        return profile, confidence

    @classmethod
    def _extract_docx(cls, file_bytes: bytes) -> str:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return '\n'.join(p.text.strip() for p in doc.paragraphs if p.text.strip())

    @classmethod
    def _extract_pdf(cls, file_bytes: bytes) -> str:
        import pdfplumber
        lines = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    lines.append(page_text)
        return '\n'.join(lines)

    @classmethod
    def parse_text(cls, text: str) -> Dict[str, Any]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        contact = cls._extract_contact(lines)
        sections = cls._split_sections(lines)
        experience = cls._parse_experience(sections.get('experience', []))
        education = cls._parse_education(sections.get('education', []))
        skills = cls._parse_skills(sections.get('skills', []))
        summary_variants = cls._parse_summary(sections.get('summary', []))
        projects = cls._parse_projects(sections.get('projects', []))
        headline = cls._guess_headline(lines, contact)

        return {
            'contact': contact,
            'headline': headline,
            'summary_variants': summary_variants,
            'experience': experience,
            'education': education,
            'skills': skills,
            'projects': projects,
        }

    @classmethod
    def _extract_contact(cls, lines: List[str]) -> Dict[str, str]:
        header = ' '.join(lines[:8])
        contact = {
            'name': lines[0] if lines else '',
            'email': '',
            'phone': '',
            'location': '',
            'linkedin': '',
        }
        email = cls.EMAIL_PATTERN.search(header)
        if email:
            contact['email'] = email.group(0)
        phone = cls.PHONE_PATTERN.search(header)
        if phone:
            contact['phone'] = phone.group(0).strip()
        linkedin = cls.LINKEDIN_PATTERN.search(header)
        if linkedin:
            contact['linkedin'] = linkedin.group(0)
        for line in lines[1:6]:
            if '@' not in line and not cls.PHONE_PATTERN.search(line) and 'linkedin' not in line.lower():
                if len(line) < 80 and ',' in line:
                    contact['location'] = line
                    break
        return contact

    @classmethod
    def _split_sections(cls, lines: List[str]) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current = 'header'
        sections[current] = []
        for line in lines:
            matched = None
            for name, pattern in cls.SECTION_PATTERNS.items():
                if pattern.match(line.strip()):
                    matched = name
                    break
            if matched:
                current = matched
                sections.setdefault(current, [])
            else:
                sections.setdefault(current, []).append(line)
        return sections

    @classmethod
    def _parse_summary(cls, lines: List[str]) -> List[Dict[str, Any]]:
        if not lines:
            return []
        text = ' '.join(lines)
        return [{'id': str(uuid.uuid4()), 'text': text, 'tags': []}]

    @classmethod
    def _parse_experience(cls, lines: List[str]) -> List[Dict[str, Any]]:
        entries = []
        current = None
        for line in lines:
            if cls.BULLET_PATTERN.match(line):
                if current:
                    bullet_text = cls.BULLET_PATTERN.sub('', line).strip()
                    current['bullets'].append({
                        'id': str(uuid.uuid4()),
                        'text': bullet_text,
                        'skills': cls._extract_skills_from_text(bullet_text),
                        'metrics': bool(re.search(r'\d+%?|\$[\d,]+|\d+\+?', bullet_text)),
                    })
            elif cls.DATE_PATTERN.search(line) or (current and len(line) < 120):
                if current and current.get('bullets'):
                    entries.append(current)
                title, company, start, end = cls._parse_role_line(line)
                current = {
                    'id': str(uuid.uuid4()),
                    'company': company,
                    'title': title,
                    'start': start,
                    'end': end,
                    'location': '',
                    'bullets': [],
                }
            elif current:
                current['bullets'].append({
                    'id': str(uuid.uuid4()),
                    'text': line,
                    'skills': cls._extract_skills_from_text(line),
                    'metrics': bool(re.search(r'\d+%?|\$[\d,]+|\d+\+?', line)),
                })
        if current:
            entries.append(current)
        return entries

    @classmethod
    def _parse_role_line(cls, line: str) -> Tuple[str, str, str, str]:
        date_match = cls.DATE_PATTERN.search(line)
        start, end = '', ''
        remainder = line
        if date_match:
            start = date_match.group(1)
            end = date_match.group(2)
            remainder = line[:date_match.start()].strip(' ,|–—-')
        parts = re.split(r'\s+at\s+|\s+\|\s+|,\s+', remainder, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip(), start, end
        return remainder, '', start, end

    @classmethod
    def _parse_education(cls, lines: List[str]) -> List[Dict[str, Any]]:
        entries = []
        for line in lines:
            entries.append({
                'id': str(uuid.uuid4()),
                'institution': line,
                'degree': '',
                'field': '',
                'start': '',
                'end': '',
            })
        return entries

    @classmethod
    def _parse_skills(cls, lines: List[str]) -> Dict[str, List[str]]:
        text = ' '.join(lines)
        technical = [s.strip() for s in re.split(r'[,;|•\n]', text) if s.strip()]
        return {'technical': technical, 'certifications': []}

    @classmethod
    def _parse_projects(cls, lines: List[str]) -> List[Dict[str, Any]]:
        return [{'id': str(uuid.uuid4()), 'name': line, 'description': '', 'skills': []} for line in lines]

    @classmethod
    def _guess_headline(cls, lines: List[str], contact: Dict[str, str]) -> str:
        for line in lines[1:5]:
            if line == contact.get('name'):
                continue
            if '@' in line or cls.PHONE_PATTERN.search(line):
                continue
            if len(line) < 80:
                return line
        return ''

    @classmethod
    def _extract_skills_from_text(cls, text: str) -> List[str]:
        common = [
            'python', 'java', 'javascript', 'typescript', 'react', 'node', 'sql',
            'postgresql', 'aws', 'docker', 'kubernetes', 'flask', 'django', 'fastapi',
            'redis', 'celery', 'git', 'linux', 'agile', 'scrum', 'rest', 'api',
        ]
        lower = text.lower()
        return [skill for skill in common if skill in lower]

    @classmethod
    def _estimate_confidence(cls, profile: Dict[str, Any]) -> float:
        score = 0.0
        contact = profile.get('contact', {})
        if contact.get('email'):
            score += 20
        if contact.get('name'):
            score += 15
        if profile.get('experience'):
            score += 35
        if profile.get('education'):
            score += 15
        if profile.get('skills', {}).get('technical'):
            score += 15
        return min(score, 100.0)

    @classmethod
    def validate_profile(cls, profile: Dict[str, Any]) -> List[str]:
        errors = []
        contact = profile.get('contact', {})
        if not contact.get('name'):
            errors.append('Contact name is required.')
        if not contact.get('email'):
            errors.append('Contact email is required.')
        if not profile.get('experience'):
            errors.append('At least one experience entry is required.')
        return errors


resume_parser_service = ResumeParserService()
