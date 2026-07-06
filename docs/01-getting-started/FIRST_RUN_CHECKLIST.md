# First Run Checklist

Verify your Job Seeker Automation App installation is working correctly.

## Prerequisites

- Completed [Getting Started](GETTING_STARTED.md) setup
- Application running at http://localhost:5000
- Logged in as `admin@example.com` / `admin123`

## Core Functionality

### 1. Dashboard loads

- [ ] Navigate to http://localhost:5000
- [ ] Dashboard shows overview page
- [ ] Sidebar displays Job Seeker section (Overview, Resume, Jobs, Applications, Analytics)
- [ ] No error messages or missing styles

### 2. Master profile upload

- [ ] Go to **Resume → Upload Resume** (`/resume/upload`)
- [ ] Upload a PDF or DOCX resume
- [ ] Review page shows parsed JSON with contact, experience, education, skills
- [ ] Save profile successfully
- [ ] Profile appears in **Resume → Master Profile** (`/resume/profiles`) as active

### 3. Manual job posting

- [ ] Go to **Jobs → Add Job** (`/jobs/postings/new`)
- [ ] Create a job posting with title, company, and description
- [ ] Posting appears in **Jobs → Job Postings** (`/jobs/postings`)
- [ ] Posting detail shows keyword analysis vs your active profile

### 4. Create application

- [ ] From posting detail, click **Create Application**
- [ ] Application appears in **Applications → All Applications** (`/applications/list`)
- [ ] Application detail shows stage `saved`

### 5. Tailor resume

- [ ] From application detail, click **Tailor Resume**
- [ ] Application stage changes to `tailoring`
- [ ] Tailoring review page (`/applications/<id>/tailoring`) shows diff, keywords, resume preview
- [ ] ATS parse-test score displayed (should be ≥ 70)

### 6. Approve and apply review

- [ ] Click **Approve Resume**
- [ ] Application stage changes to `ready_to_apply`
- [ ] Apply review page (`/apply/<id>`) shows form fields, cover letter, resume preview
- [ ] Download DOCX resume works
- [ ] Download cover letter works

### 7. Mark as applied

- [ ] Click **Mark as Applied**
- [ ] Application stage changes to `applied`
- [ ] Activity timeline shows submission event

### 8. Pipeline kanban

- [ ] Go to **Applications → Pipeline** (`/applications/pipeline`)
- [ ] Application card visible in `applied` column
- [ ] Drag card to another stage (e.g. `interview`) — stage updates

### 9. Analytics

- [ ] Go to **Analytics** (`/analytics/`)
- [ ] Dashboard shows at least one application in funnel
- [ ] No errors loading metrics

## API Verification

### 10. API health

```bash
curl http://localhost:5000/api/v1/health
```

- [ ] Returns healthy status

### 11. API with session

```bash
# List profiles (requires login cookie)
curl -b cookies.txt http://localhost:5000/api/v1/resume/profiles
```

- [ ] Returns profile list with your uploaded profile

### 12. Swagger UI

- [ ] Navigate to http://localhost:5000/api/v1/docs/
- [ ] Swagger page loads with job seeker API endpoints

## Database Verification

### 13. Tables exist

```bash
python scripts/check_database_tables.py
```

- [ ] `master_profiles` table exists
- [ ] `job_postings` table exists
- [ ] `applications` table exists
- [ ] `discovered_jobs` table exists
- [ ] `portal_credentials` table exists
- [ ] `apply_batches` table exists

If any jobs tables are missing:
```bash
python scripts/create_jobs_schema.py
```

## Optional: Automation Features

Skip this section for basic local dev. Complete when enabling automation.

### 14. Credential encryption key

- [ ] `CREDENTIAL_ENCRYPTION_KEY` set in `.env`
- [ ] Application restarted after setting key

### 15. Playwright

```bash
playwright install chromium
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

- [ ] Playwright imports and Chromium installed

### 16. LLM tailoring (optional)

- [ ] `OPENAI_API_KEY` set in `.env`
- [ ] Tailoring produces nuanced rephrasing (not just heuristic changes)
- [ ] Cover letter is context-aware (not template text)

### 17. Discovery (optional)

- [ ] Search profile created at `/jobs/search-profiles/new`
- [ ] Discovery run completes without errors
- [ ] Jobs appear in inbox at `/jobs/inbox` (API sources like Remotive work without credentials)

### 18. Portal credentials (optional)

- [ ] Session exported: `python scripts/export_playwright_storage.py linkedin`
- [ ] Credentials saved at `/apply/credentials`
- [ ] Test button reports healthy session

## Test Suite

### 19. Run tests

```bash
pytest
```

- [ ] All tests pass (or only expected skips for Playwright live tests)

Targeted job seeker tests:
```bash
pytest tests/test_resume_export_service.py tests/test_tailoring_diff_service.py tests/test_apply_draft_service.py -v
```

- [ ] Job seeker service tests pass

## Production Readiness (if deploying)

- [ ] `SECRET_KEY` and `JWT_SECRET_KEY` changed from defaults
- [ ] `FLASK_DEBUG=False` and `FLASK_ENV=production`
- [ ] PostgreSQL configured (not SQLite)
- [ ] `CREDENTIAL_ENCRYPTION_KEY` set
- [ ] Auto-apply flags remain disabled until tested
- [ ] Database backup configured
- [ ] HTTPS configured via reverse proxy

See [Admin Guide](../04-operations/ADMIN_GUIDE.md) for production checklist.

## All Checks Pass?

You're ready to use the application. Next steps:

1. **Job seeker:** Follow the [full workflow](../02-user-guide/WORKFLOW.md)
2. **Administrator:** Configure [automation](../04-operations/AUTOMATION_SETUP.md) if needed
3. **Developer:** Explore the [service layer](../02-architecture/JOB_SEEKER_SERVICES.md)

## Something Failed?

| Symptom | Fix |
|---------|-----|
| Tables missing | `python scripts/create_jobs_schema.py` |
| Upload fails | Check file is PDF/DOCX; check logs |
| Tailoring empty | Ensure active master profile exists |
| Styles broken | Check `app/static/` assets present |
| API 401 | Log in first; check session cookie |
| Tests fail | `pip install -r requirements/requirements-dev.txt` |

See [Troubleshooting](../04-operations/TROUBLESHOOTING.md) for detailed solutions.

## Related Docs

- [Getting Started](GETTING_STARTED.md)
- [User Guide](../02-user-guide/WORKFLOW.md)
- [Automation Setup](../04-operations/AUTOMATION_SETUP.md)
