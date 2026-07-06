# ATS Export Rules

Rules enforced when exporting resumes to DOCX for Applicant Tracking Systems (ATS). Source: [`app/services/resume_export_service.py`](../../app/services/resume_export_service.py).

## Prerequisites

- Active master profile or approved tailored resume — see [MASTER_PROFILE.md](../02-user-guide/MASTER_PROFILE.md)
- Understanding of tailoring workflow — see [TAILORING_AND_APPLY.md](../02-user-guide/TAILORING_AND_APPLY.md)

## Purpose

ATS systems parse uploaded resumes to extract structured data. Poorly formatted resumes lose information during parsing, reducing match scores and visibility to recruiters. This application enforces ATS-safe formatting on every export and runs an automated parse-test to score readability.

## Format Rules (Enforced on Export)

### Layout

| Rule | Requirement | Rationale |
|------|-------------|-----------|
| Single column | No multi-column layouts | ATS parsers read top-to-bottom |
| No tables | Zero layout tables | Tables break text extraction |
| No graphics | No images, charts, or icons | ATS cannot read visual content |
| No headers/footers | Contact info in document body | Headers/footers are often stripped |

### Typography

| Element | Setting |
|---------|---------|
| Font | Calibri (all text) |
| Name | 16pt, bold |
| Section headings | 12pt, bold, uppercase |
| Body text | 11pt |
| Color | Black (RGB 0,0,0) |

### Sections

Exports include these sections in order (empty sections are omitted):

1. **Contact block** — Name, headline, email, phone, location, LinkedIn (pipe-separated)
2. **Summary** — Professional summary text
3. **Experience** — Role entries with bullets
4. **Education** — Degree and institution entries
5. **Skills** — Comma-separated technical skills and certifications

Section headings use uppercase labels: `SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`.

### Experience Format

Each experience entry renders as:

```
Job Title | Company | Start - End
  • Bullet point one
  • Bullet point two
```

- Role line is bold
- Maximum 5 bullets per role in DOCX export (8 in text preview)
- Standard Word bullet style (`List Bullet`)
- End date defaults to `Present` if not set

### Skills Format

Technical skills and certifications are combined into a single comma-separated line under the `SKILLS` heading. No skill bars, ratings, or category groupings.

### File Naming

Generated filename pattern:

```
FirstName_LastName_Role_Company.docx
```

- Spaces replaced with underscores
- Uses contact name, headline (role), and target company if available
- Maximum three name parts

Example: `Jane_Smith_Senior_Engineer_Acme_Corp.docx`

## Parse-Test Harness

Every export can be validated with `run_ats_parse_test()`. The harness opens the generated DOCX and checks extractability.

### Scoring

Starting score: **100 points**. Deductions apply for failures:

| Check | Pass | Fail deduction |
|-------|------|----------------|
| Has Experience section | +0 | −15 |
| Has Education section | +0 | −15 |
| Has Skills section | +0 | −15 |
| No layout tables | +0 | −20 |
| Minimum content length (≥100 chars) | +0 | −25 |
| Email found in document body | +0 | −10 |

**Pass threshold:** score ≥ 70

### Check Details

| Rule ID | Description |
|---------|-------------|
| `has_experience_section` | Text contains "experience" |
| `has_education_section` | Text contains "education" |
| `has_skills_section` | Text contains "skills" |
| `simple_bullets` | No exotic Unicode bullet characters |
| `no_tables` | Document contains zero tables |
| `min_content` | Extractable text length ≥ 100 characters |
| `contact_in_body` | Email address regex found in body text |
| `parseable` | DOCX opens without error |

### Viewing Results

ATS parse-test results appear on:

- Master profile detail page (`/resume/profiles/<id>`)
- Tailoring review page (`/applications/<id>/tailoring`)
- Apply review page (`/apply/<id>`) — resume preview section

Results include overall score, pass/fail status, and per-check messages.

## Cover Letter Export

Cover letters export as separate DOCX files:

- Same Calibri font
- Paragraphs split on double newlines
- Filename: `Cover_Letter.docx` (or custom)
- Also available as plain text download

## Text Preview

`render_preview_text()` generates a plain-text preview of the DOCX content. This shows exactly what text an ATS would extract, without formatting. Available on apply review and tailoring pages.

## What Tailoring Can and Cannot Change

Tailoring operates on the structured `profile_data` JSON. Export rules apply to the output regardless of whether the source is master profile or tailored version.

| Allowed | Not allowed |
|---------|-------------|
| Reorder experience bullets | Invent new jobs or employers |
| Rephrase bullet text | Add skills you don't have |
| Emphasize relevant experience | Change dates or titles falsely |
| Select summary variant | Add tables, graphics, or columns |
| Reorder skills list | Use non-Calibri fonts |

See [TAILORING_AND_APPLY.md](../02-user-guide/TAILORING_AND_APPLY.md) for the full tailoring review process.

## Tips for High ATS Scores

1. **Complete all sections** — Empty experience, education, or skills sections reduce score
2. **Include email in contact** — Must appear in document body, not a header
3. **Use standard bullets** — Avoid copy-pasting from web pages with exotic characters
4. **Keep content substantial** — Very short resumes fail the minimum content check
5. **Review parse-test after tailoring** — Re-run after significant edits

## API Usage

```python
from app.services.resume_export_service import resume_export_service

# Export DOCX
docx_bytes, filename = resume_export_service.export_docx(profile_data)

# Run parse test
result = resume_export_service.run_ats_parse_test(docx_bytes)
# result = {"score": 95.0, "checks": [...], "passed": True}

# Text preview
preview = resume_export_service.render_preview_text(profile_data)
```

## Related Docs

- [MASTER_PROFILE.md](../02-user-guide/MASTER_PROFILE.md) — Upload and manage profiles
- [TAILORING_AND_APPLY.md](../02-user-guide/TAILORING_AND_APPLY.md) — Tailoring and download
- [JOB_SEEKER_DATA_MODEL.md](JOB_SEEKER_DATA_MODEL.md) — ResumeVersion.ats_score field
- [JOB_SEEKER_API.md](../03-development/JOB_SEEKER_API.md) — Resume export API endpoints
