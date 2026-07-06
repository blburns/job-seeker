# Master Profile

Upload, review, edit, and export your structured resume profile.

## Prerequisites

- Logged in to the application
- A resume file (PDF or DOCX) or willingness to enter data manually

## What Is a Master Profile?

Your master profile is the canonical version of your resume stored as structured JSON. Every tailoring operation starts from this profile. The master profile itself is never modified by tailoring — changes are saved as separate resume versions.

## Upload a Resume

### Step 1: Navigate to upload

Go to **Resume → Upload Resume** (`/resume/upload`).

### Step 2: Select file

Choose a PDF or DOCX file. The parser extracts:
- Contact information (name, email, phone, location, LinkedIn)
- Professional headline
- Summary
- Work experience (title, company, dates, bullets)
- Education (institution, degree, dates)
- Skills (technical, certifications)

### Step 3: Review parsed data

After upload, you land on the review page (`resume/review.html`):

- Parsed JSON displayed for inspection
- Parse confidence score shown
- Edit the JSON directly to fix parsing errors
- Common fixes: missing bullets, incorrect dates, misidentified sections

### Step 4: Save

Click **Save Profile**. The profile is created and set as your **active** master profile.

## Create a Profile Manually

If you don't have a file to upload:

1. Go to **Resume → Create Profile** (`/resume/profiles/manual`)
2. Fill in the structured form (contact, experience, education, skills)
3. Save

Manual profiles have `source_type: manual`.

## Manage Profiles

### Profile list

**Resume → Master Profile** (`/resume/profiles`) shows all your profiles:
- Active profile marked with a badge
- Source type (PDF, DOCX, manual)
- Headline and creation date

### Profile detail

Click a profile to open `/resume/profiles/<id>`:
- Full profile data display
- ATS parse-test score (run against a DOCX export)
- Activate, edit, or delete actions

### Activate a profile

Only one profile is active at a time. The active profile drives:
- Keyword analysis on job postings
- Fit scoring in discovery
- Tailoring for new applications

To switch: click **Activate** on the profile you want (`POST /resume/profiles/<id>/activate`).

### Edit a profile

Two edit modes:
- **JSON editor** — `/resume/profiles/<id>/edit` — Direct JSON editing
- **Form editor** — `/resume/profiles/<id>/manual` — Structured form fields

### Delete a profile

Soft delete via `/resume/profiles/<id>/delete`. Deleted profiles are hidden but not permanently removed.

## ATS Export

Every profile can be exported to an ATS-safe DOCX file. See [ATS_EXPORT_RULES.md](../05-reference/ATS_EXPORT_RULES.md) for format details.

### Export rules summary

- Single column, Calibri font
- Standard sections: Summary, Experience, Education, Skills
- No tables, graphics, or headers/footers
- Contact info in document body
- Filename: `FirstName_LastName_Role_Company.docx`

### Parse-test

The profile detail page runs an ATS parse-test that scores the export:
- Checks for required sections (experience, education, skills)
- Verifies no layout tables
- Confirms email in document body
- Pass threshold: score ≥ 70

### Download

Download DOCX from profile detail or from the apply review page after tailoring.

## Profile Data Structure

```json
{
  "contact": {
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1 555-0100",
    "location": "San Francisco, CA",
    "linkedin": "linkedin.com/in/janesmith"
  },
  "headline": "Senior Software Engineer",
  "summary": "Experienced engineer with 10+ years...",
  "summary_variants": [
    {"text": "Backend-focused engineer..."},
    {"text": "Full-stack leader..."}
  ],
  "experience": [
    {
      "title": "Senior Engineer",
      "company": "Acme Corp",
      "start": "2020-01",
      "end": "Present",
      "bullets": [
        {"text": "Led migration of monolith to microservices"},
        {"text": "Reduced API latency by 40%"}
      ]
    }
  ],
  "education": [
    {
      "institution": "State University",
      "degree": "BS Computer Science",
      "end": "2014"
    }
  ],
  "skills": {
    "technical": ["Python", "PostgreSQL", "AWS"],
    "certifications": ["AWS Solutions Architect"]
  }
}
```

## Tips

1. **Upload the simplest format** — Single-column resumes parse best
2. **Review immediately after upload** — Fix parsing errors before saving
3. **Add summary variants** — Tailoring selects the best variant per job
4. **Keep skills comprehensive** — More skills = better keyword coverage
5. **Run parse-test after edits** — Verify ATS score stays above 70
6. **One active profile** — Ensure the right profile is active before discovery or tailoring

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low parse confidence | Upload a simpler format; edit JSON manually |
| Missing experience bullets | Add bullets in JSON or form editor |
| ATS score below 70 | Ensure all sections populated; check email in contact |
| Wrong active profile | Activate the correct profile from the list |

## Related Docs

- [CONCEPTS.md](CONCEPTS.md) — Master profile concept
- [ATS_EXPORT_RULES.md](../05-reference/ATS_EXPORT_RULES.md) — Export format rules
- [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md) — How tailoring uses your profile
- [WORKFLOW.md](WORKFLOW.md) — Where profile fits in the workflow
