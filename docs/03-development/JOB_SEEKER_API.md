# Job Seeker API Reference

REST API endpoints for the job seeker modules. Interactive documentation available at `/api/v1/docs/` (Swagger UI).

## Prerequisites

- Authenticated session (Flask-Login) or JWT token
- See [AUTHENTICATION.md](auth/AUTHENTICATION.md) for auth details

## Base URLs

| Module | Prefix |
|--------|--------|
| Resume | `/api/v1/resume` |
| Jobs | `/api/v1/jobs` |
| Applications | `/api/v1/applications` |
| Apply | `/api/v1/apply` |

All endpoints require authentication (`@login_required`) unless noted.

## Resume API

**Blueprint:** `app/modules/resume/api.py`

### List profiles

```
GET /api/v1/resume/profiles
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "headline": "Senior Software Engineer",
      "is_active": true,
      "source_type": "pdf",
      "parse_confidence": 85.5,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Get profile

```
GET /api/v1/resume/profiles/<profile_id>
```

Returns full profile including `profile_data` JSON.

### Upload and parse

```
POST /api/v1/resume/upload
Content-Type: multipart/form-data
```

**Body:** `file` — PDF, DOCX, or TXT

**Response:**
```json
{
  "profile_data": { "contact": {}, "experience": [], ... },
  "parse_confidence": 85.5,
  "validation_errors": [],
  "parse_diagnostics": {},
  "source_filename": "resume.pdf"
}
```

### Save profile

```
POST /api/v1/resume/profiles
Content-Type: application/json
```

**Body:**
```json
{
  "profile_data": { "contact": {}, "experience": [], ... },
  "source_filename": "resume.pdf",
  "source_type": "pdf",
  "parse_confidence": 85.5
}
```

Deactivates other profiles and sets this one as active. Returns `201` with profile dict.

### Update profile

```
PATCH /api/v1/resume/profiles/<profile_id>
Content-Type: application/json
```

**Body:** Partial update with `profile_data`, `headline`, or `notes`.

### Delete profile

```
DELETE /api/v1/resume/profiles/<profile_id>
```

Soft delete.

### Activate profile

```
POST /api/v1/resume/profiles/<profile_id>/activate
```

Sets profile as active; deactivates others.

### Export DOCX

```
GET /api/v1/resume/profiles/<profile_id>/export
```

Returns DOCX file download.

### ATS parse test

```
POST /api/v1/resume/profiles/<profile_id>/ats-test
```

**Response:**
```json
{
  "score": 95.0,
  "checks": [
    {"rule": "has_experience_section", "passed": true, "message": "Found experience section"}
  ],
  "passed": true
}
```

---

## Jobs API

**Blueprint:** `app/modules/jobs/api.py`

### List postings

```
GET /api/v1/jobs/postings
```

Query params: `source`, `company`, `is_active`

### Create posting

```
POST /api/v1/jobs/postings
Content-Type: application/json
```

**Body:**
```json
{
  "title": "Senior Engineer",
  "company": "Acme Corp",
  "description": "Full job description...",
  "location": "Remote",
  "url": "https://example.com/job/123",
  "source": "manual"
}
```

### Fetch from URL

```
POST /api/v1/jobs/postings/fetch-url
Content-Type: application/json
```

**Body:** `{"url": "https://example.com/job/123"}`

Returns parsed job fields.

### Get posting

```
GET /api/v1/jobs/postings/<posting_id>
```

### Update posting

```
PATCH /api/v1/jobs/postings/<posting_id>
```

### Keyword analysis

```
GET /api/v1/jobs/postings/<posting_id>/keywords
```

**Response:**
```json
{
  "jd_keywords": ["python", "kubernetes"],
  "matched_keywords": ["python"],
  "missing_keywords": ["kubernetes"],
  "coverage_score": 50.0
}
```

### Search profiles

```
GET /api/v1/jobs/search-profiles
POST /api/v1/jobs/search-profiles
PATCH /api/v1/jobs/search-profiles/<profile_id>
DELETE /api/v1/jobs/search-profiles/<profile_id>
```

**Create body:**
```json
{
  "name": "Senior Backend - Remote",
  "titles": ["Senior Software Engineer"],
  "locations": ["Remote"],
  "remote_preference": "remote",
  "sources": ["adzuna", "remotive"],
  "min_fit_score": 50
}
```

### Run discovery

```
POST /api/v1/jobs/search-profiles/<profile_id>/run
```

Triggers discovery for all enabled sources. Returns run summary.

### Discovery inbox

```
GET /api/v1/jobs/inbox
```

Returns discovered jobs with status `new`, sorted by fit score.

### Accept discovered job

```
POST /api/v1/jobs/inbox/<discovered_id>/accept
```

Creates `JobPosting` + `Application`. Returns both records.

### Skip discovered job

```
POST /api/v1/jobs/inbox/<discovered_id>/skip
```

### RSS discovery

```
POST /api/v1/jobs/discover/rss
POST /api/v1/jobs/discover/rss/save
```

---

## Applications API

**Blueprint:** `app/modules/applications/api.py`

### List applications

```
GET /api/v1/applications/
```

Query params: `stage`, `company`

### Create application

```
POST /api/v1/applications/
Content-Type: application/json
```

**Body:**
```json
{
  "job_posting_id": "uuid",
  "notes": "Found via LinkedIn"
}
```

### Get application

```
GET /api/v1/applications/<application_id>
```

Returns application with job posting, resume version, and activities.

### Pipeline view

```
GET /api/v1/applications/pipeline
```

**Response:**
```json
{
  "saved": [...],
  "tailoring": [...],
  "ready_to_apply": [...],
  "applied": [...],
  "phone_screen": [...],
  "interview": [...],
  "offer": [...]
}
```

### Update stage

```
PATCH /api/v1/applications/<application_id>/stage
Content-Type: application/json
```

**Body:** `{"stage": "interview"}`

Used by pipeline kanban drag-and-drop.

### Tailor resume

```
POST /api/v1/applications/<application_id>/tailor
```

Creates `ResumeVersion`, runs keyword analysis, seeds apply draft. Returns resume version and keyword analysis.

### Approve resume

```
POST /api/v1/applications/<application_id>/approve
```

Sets resume version to `approved`, stage to `ready_to_apply`, regenerates apply draft.

---

## Apply API

**Blueprint:** `app/modules/apply/api.py`

### Get apply draft

```
GET /api/v1/apply/drafts/<application_id>
```

Returns form fields, cover letter, and status.

### Save apply draft

```
POST /api/v1/apply/drafts/<application_id>
Content-Type: application/json
```

**Body:**
```json
{
  "form_fields": {"name": "Jane Smith", "email": "jane@example.com"},
  "cover_letter": "Dear Hiring Manager..."
}
```

### Approve draft

```
POST /api/v1/apply/drafts/<draft_id>/approve
```

### Submit application

```
POST /api/v1/apply/submit/<application_id>
```

Manual submission — marks application as applied.

### Create batch

```
POST /api/v1/apply/batches
Content-Type: application/json
```

**Body:**
```json
{
  "application_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### Approve batch

```
POST /api/v1/apply/batches/<batch_id>/approve
```

Triggers Celery submission task (or sync in local dev).

### Batch status

```
GET /api/v1/apply/batches/<batch_id>/status
```

Returns batch status and per-item submission results.

---

## Error Responses

All endpoints return standard error format:

```json
{
  "error": "Description of the error",
  "details": {}
}
```

| Status | Meaning |
|--------|---------|
| 400 | Validation error or bad request |
| 401 | Not authenticated |
| 403 | Permission denied |
| 404 | Resource not found |
| 500 | Server error |

## Authentication

### Session-based (web)

Log in via `/auth/login`. Session cookie sent automatically.

### JWT (API)

```
POST /api/v1/auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "password"}
```

Use returned token in `Authorization: Bearer <token>` header.

## Code Examples

### Python: Upload and save profile

```python
import requests

session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'email': 'admin@example.com', 'password': 'admin123'
})

with open('resume.pdf', 'rb') as f:
    resp = session.post('http://localhost:5000/api/v1/resume/upload', files={'file': f})
    parsed = resp.json()

session.post('http://localhost:5000/api/v1/resume/profiles', json={
    'profile_data': parsed['profile_data'],
    'source_filename': 'resume.pdf',
    'source_type': 'pdf',
    'parse_confidence': parsed['parse_confidence'],
})
```

### Python: Run discovery and accept job

```python
# Run discovery
session.post(f'http://localhost:5000/api/v1/jobs/search-profiles/{profile_id}/run')

# Get inbox
inbox = session.get('http://localhost:5000/api/v1/jobs/inbox').json()

# Accept first job
if inbox['data']:
    job_id = inbox['data'][0]['id']
    session.post(f'http://localhost:5000/api/v1/jobs/inbox/{job_id}/accept')
```

### cURL: Tailor and approve

```bash
# Tailor
curl -X POST http://localhost:5000/api/v1/applications/$APP_ID/tailor \
  -H "Cookie: session=..." 

# Approve
curl -X POST http://localhost:5000/api/v1/applications/$APP_ID/approve \
  -H "Cookie: session=..."
```

## Related Docs

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — General API framework (boilerplate)
- [AUTHENTICATION.md](auth/AUTHENTICATION.md) — Auth system
- [JOB_SEEKER_SERVICES.md](../02-architecture/JOB_SEEKER_SERVICES.md) — Service layer
- [JOB_SEEKER_DATA_MODEL.md](../05-reference/JOB_SEEKER_DATA_MODEL.md) — Data models
