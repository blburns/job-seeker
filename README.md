# Job Seeker Automation App

Semi-automated job application platform built on Flask + Vuexy + Tailwind. Ingest your resume into a structured master profile, tailor it per job posting with ATS-safe exports, track applications in a kanban pipeline, and review pre-filled application drafts before submitting.

**[Full Documentation →](docs/README.md)**

## Who Is This For?

| Role | Quick start |
|------|-------------|
| **Job seeker** | [User Guide](docs/02-user-guide/WORKFLOW.md) — upload resume, find jobs, tailor, apply, track |
| **Administrator** | [Admin Guide](docs/04-operations/ADMIN_GUIDE.md) — users, automation, deployment |
| **Developer** | [Architecture](docs/02-architecture/ARCHITECTURE.md) — services, API, scraping |

## Features

- **Master Profile** — Upload PDF/DOCX, parse into structured JSON, human review before save
- **Job Discovery** — Automated search (Adzuna, Remotive, Greenhouse, Lever, RSS, Indeed, LinkedIn) with fit-scored inbox
- **Keyword Analysis** — JD term extraction, matched/missing coverage map
- **Constrained Tailoring** — Reorder, rephrase, emphasize — never invent facts; full diff audit trail
- **ATS Export** — Single-column DOCX with parse-test harness and scoring
- **Application Pipeline** — Kanban board (Saved → Tailoring → Ready → Applied → Interview → Offer)
- **Apply Pre-fill** — Side-by-side JD keywords, tailored resume, form fields for review
- **Batch Auto-Apply** — Group approved applications for portal submission (disabled by default)
- **Analytics** — Pipeline funnel, response rates, source effectiveness

## Quick Start (local — no Docker)

```bash
cp env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements/requirements.txt -r requirements/requirements-jobs.txt
playwright install chromium   # or use PLAYWRIGHT_CHANNEL=chrome with Google Chrome installed
python scripts/init_database.py
python scripts/create_jobs_schema.py
python scripts/create_dev_user.py   # admin@example.com / admin123
python run.py
```

Open http://localhost:5000 and log in.

**Local dev does not require Redis, Celery, or Docker.** Discovery runs in the Flask process when you click "Run discovery" on a search profile.

### Docker (optional)

For production-style deployments with Redis, Celery workers, and scheduled discovery:

```bash
docker compose up --build
python scripts/init_database.py
python scripts/create_jobs_schema.py
python scripts/create_dev_user.py
```

## Workflow

1. Upload resume → review parsed JSON → save master profile
2. Find jobs → automated discovery or manual add
3. Create application → tailor resume → review changes → approve
4. Review pre-fill draft → download DOCX → submit (manual or batch)
5. Track progress on pipeline kanban → view analytics

See [full workflow guide](docs/02-user-guide/WORKFLOW.md).

## API Endpoints

| Module | Prefix |
|--------|--------|
| Resume | `/api/v1/resume` |
| Jobs | `/api/v1/jobs` |
| Applications | `/api/v1/applications` |
| Apply | `/api/v1/apply` |

Swagger UI at `/api/v1/docs/`. See [API reference](docs/03-development/JOB_SEEKER_API.md).

## ATS Rules (enforced in export)

- Single column, standard headings (Experience, Education, Skills, Summary)
- Calibri font, simple bullets, contact in body not header/footer
- No tables, graphics, or keyword stuffing
- File naming: `FirstName_LastName_Role_Company.docx`

See [ATS export rules](docs/05-reference/ATS_EXPORT_RULES.md).

## Documentation

| Section | Contents |
|---------|----------|
| [User Guide](docs/02-user-guide/) | End-user walkthroughs |
| [Getting Started](docs/01-getting-started/) | Installation and setup |
| [Architecture](docs/02-architecture/) | System design and services |
| [Development](docs/03-development/) | API, scraping, modules |
| [Operations](docs/04-operations/) | Admin, deployment, config |
| [Reference](docs/05-reference/) | Data model, ATS rules |

## Stack

- Flask, SQLAlchemy, Flask-Login, RBAC (from boilerplate-crm)
- Vuexy admin template, Tailwind CSS
- python-docx, pdfplumber, Playwright
- OpenAI API (optional, for LLM tailoring)
- PostgreSQL (production) or SQLite (local dev)
- Celery + Redis (optional, for background tasks)

## Version

v0.2.0 — Phase 2: Core Services

## License

Licensed under the [Apache License, Version 2.0](LICENSE).

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the path to v1.0 production release.
