# Tailoring and Apply Review

Tailor your resume for a specific job and review the pre-filled application draft before submitting.

## Prerequisites

- Application at stage `saved` — see [APPLICATIONS.md](APPLICATIONS.md)
- Active master profile — see [MASTER_PROFILE.md](MASTER_PROFILE.md)

## Tailoring

### What tailoring does

Tailoring creates a job-specific resume version from your master profile:

| Action | Description |
|--------|-------------|
| Set headline | Updates to match job title |
| Select summary | Picks best summary variant for JD keywords |
| Rephrase bullets | Includes missing keywords naturally (max 5 changes) |
| Reorder bullets | Moves most relevant experience to top |
| Reorder skills | Prioritizes matching skills |

**What tailoring never does:**
- Invent new jobs, companies, or dates
- Add skills you don't have
- Fabricate metrics or achievements
- Change your contact information

### Run tailoring

From application detail (`/applications/<id>`):

1. Click **Tailor Resume** (`POST /applications/<id>/tailor`)
2. Wait for processing (seconds with LLM; instant with heuristic fallback)
3. Application stage changes to `tailoring`
4. Resume version created with status `pending_approval`

Tailoring also:
- Runs keyword analysis (stores `KeywordAnalysis` record)
- Runs ATS parse-test on the tailored export
- Seeds an apply draft with form fields

### Batch tailoring

From the apply queue (`/applications/queue`):
1. Select multiple applications at stage `saved`
2. Click **Batch Tailor** (`POST /applications/batch-tailor`)
3. Tailoring runs in background (Celery if available; sync otherwise)

## Tailoring Review

Open `/applications/<id>/tailoring` for the full review interface.

### Tabs

| Tab | Content |
|-----|---------|
| **Overview** | Change summary, keyword impact score, ATS score |
| **Resume** | Rendered preview of tailored resume |
| **Cover Letter** | Generated cover letter draft |
| **Changes** | Detailed diff log — every field change with before/after; **Reject** restores the original |
| **Compare** | Side-by-side master profile vs tailored version |
| **Keywords** | Matched, missing, and synonym-matched keywords |
| **Bullet edits** | Rephrase-only view with per-change **Reject** |

### Reject a change

On **All changes** or **Bullet edits** (while the version is still `pending_approval`):

1. Click **Reject** next to any inaccurate edit
2. That field is restored to the pre-tailor text
3. The DOCX preview is regenerated
4. Rejected entries stay in the log (marked Rejected) for audit

You can reject bullets, headline, summary selection, and reorder changes individually before approving.

### Diff log

Each tailoring change is recorded:

```json
{
  "field": "experience[0].bullets[2].text",
  "action": "rephrase",
  "old": "Built REST APIs for internal tools",
  "new": "Built REST APIs and microservices for internal tools",
  "master_ref": "experience[0].bullets[2]",
  "keyword": "microservices"
}
```

Actions: `set`, `rephrase`, `reorder`, `select_variant`.

### Export diff report

Download a text report of all changes (`/applications/<id>/tailoring/export`).

## Approve Resume

When satisfied with the tailoring:

1. Click **Approve Resume** (`POST /applications/<id>/approve`)
2. Resume version status → `approved`
3. Application stage → `ready_to_apply`
4. Apply draft regenerated with fresh cover letter
5. Redirected to apply review page

Approval is required before submission. You cannot skip this step.

## Apply Review

Open `/apply/<id>` to review the pre-filled application.

### Layout

The apply review page (`apply/review.html`) shows:

**Left panel — Job context:**
- Job title, company, location
- Keyword coverage chart (matched vs missing)
- Job description excerpt

**Right panel — Application form:**
- Pre-filled form fields (editable)
- Cover letter editor
- Resume text preview
- Download buttons

### Form fields

Pre-filled from your master profile and job posting:
- Name, email, phone
- Work authorization
- Years of experience
- Salary expectations
- Custom fields specific to the portal

Edit any field and click **Save Draft** (`POST /apply/<id>/save-draft`).

### Cover letter

- Generated during tailoring (LLM if configured; template fallback otherwise)
- Fully editable in the text area
- **Regenerate** (`POST /apply/<id>/regenerate-cover-letter`) — Creates a new draft with LLM

### Downloads

| File | Route | Format |
|------|-------|--------|
| Tailored resume | `/apply/<id>/download-resume` | DOCX (ATS-safe) |
| Cover letter | `/apply/<id>/download-cover-letter` | TXT or DOCX |

Resume filename follows ATS rules: `FirstName_LastName_Role_Company.docx`.

### Resume preview

Text preview shows exactly what an ATS would extract from the DOCX. Compare against the job keywords panel to verify coverage.

## Manual Submission

The recommended submission path:

1. Review and edit apply draft
2. Download tailored resume DOCX
3. Download cover letter
4. Go to the employer's application portal
5. Fill in the application using your downloaded files and draft field values
6. Submit on the employer site
7. Return to the app and click **Mark as Applied** (`POST /apply/<id>/mark-applied`)
8. Application stage → `applied`

## LLM Configuration

Tailoring and cover letter generation use OpenAI when configured:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Without an API key, the app uses heuristic fallbacks:
- Bullet keyword insertion is **skipped** (avoids inventing claims like “including X”)
- Template-based cover letters
- Summary variant selection by keyword overlap
- Experience/skills reordering by keyword relevance

Set `GEMINI_API_KEY` or `OPENAI_API_KEY` for natural bullet rephrasing. Use **Reject** on any bad edit.

## Tips

1. **Review the diff log carefully** — Reject any change that misrepresents experience
2. **Check ATS score** — Should be ≥ 70 after tailoring
3. **Edit cover letter** — Always personalize before submitting
4. **Save draft before downloading** — Ensures latest edits are captured
5. **Compare keyword panels** — Missing keywords in red are opportunities to address in cover letter
6. **Regenerate cover letter** — If the first draft doesn't highlight the right experience

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tailoring seems unchanged | Check if master profile has relevant experience for the JD |
| Low keyword coverage | Add skills to master profile; rephrase bullets manually in review |
| ATS score dropped | Ensure all sections present; check for exotic characters |
| Cover letter generic | Configure OPENAI_API_KEY; edit manually; regenerate |
| Can't approve | Ensure tailoring completed; check for pending_approval status |

## Related Docs

- [ATS_EXPORT_RULES.md](../05-reference/ATS_EXPORT_RULES.md) — Export format rules
- [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md) — Automated submission alternative
- [WORKFLOW.md](WORKFLOW.md) — Full workflow context
- [CONCEPTS.md](CONCEPTS.md) — Resume version and apply draft concepts
