# Job Seeker Automation App

Semi-automated job application platform built on Flask + Vuexy + Tailwind. Ingest your resume into a structured master profile, tailor it per job posting with ATS-safe exports, track applications in a kanban pipeline, and review pre-filled application drafts before submitting.

## Features

- **Master Profile** — Upload PDF/DOCX, parse into structured JSON, human review before save
- **ATS Export** — Single-column DOCX with parse-test harness and scoring
- **Job Postings** — Manual paste, URL fetch, RSS discovery
- **Keyword Analysis** — JD term extraction, matched/missing coverage map
- **Constrained Tailoring** — Reorder, rephrase, emphasize — never invent facts; full diff audit trail
- **Application Pipeline** — Kanban board (Saved → Applied → Interview → Offer)
- **Apply Pre-fill** — Side-by-side JD keywords, tailored resume, form fields for review

## Quick Start (local — no Docker)

```bash
cp env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements/requirements.txt -r requirements/requirements-jobs.txt
playwright install chromium   # or use PLAYWRIGHT_CHANNEL=chrome with Google Chrome installed
python scripts/init_database.py
python scripts/create_dev_user.py   # admin@example.com / admin123
python run.py
```

Open http://localhost:5000 and log in.

**Local dev does not require Redis, Celery, or Docker.** Discovery and LinkedIn scraping run in the Flask process when you click "Run discovery" on a search profile. Set `CREDENTIAL_ENCRYPTION_KEY` in `.env` before storing portal sessions.

### Docker (optional)

For production-style deployments with Redis, Celery workers, and scheduled discovery:

```bash
docker compose up --build
python scripts/create_jobs_schema.py
```

## Workflow

1. Upload resume → review parsed JSON → save master profile
2. Add job posting (paste, URL, or RSS)
3. Create application → tailor resume → approve
4. Review pre-fill draft → download DOCX → mark as applied
5. Drag cards on pipeline kanban as status changes

## API Endpoints

| Module | Prefix |
|--------|--------|
| Resume | `/api/v1/resume` |
| Jobs | `/api/v1/jobs` |
| Applications | `/api/v1/applications` |
| Apply | `/api/v1/apply` |

## ATS Rules (enforced in export)

- Single column, standard headings (Experience, Education, Skills, Summary)
- Calibri font, simple bullets, contact in body not header/footer
- No tables, graphics, or keyword stuffing
- File naming: `FirstName_LastName_Role_Company.docx`

## Stack

- Flask, SQLAlchemy, Flask-Login, RBAC (from boilerplate-crm)
- Vuexy admin template, Tailwind CSS
- python-docx, pdfplumber
- PostgreSQL (production) or SQLite (local dev)
