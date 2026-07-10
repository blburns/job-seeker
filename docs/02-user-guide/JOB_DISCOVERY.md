# Job Discovery

Find jobs automatically via search profiles or add them manually.

## Prerequisites

- Active master profile — see [MASTER_PROFILE.md](MASTER_PROFILE.md)
- For LinkedIn/Indeed scraping: portal credentials configured — see [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md)

## Discovery Methods

| Method | Route | Best for |
|--------|-------|----------|
| Automated search profiles | `/jobs/search-profiles` | Ongoing job search across multiple sources |
| Discovery inbox | `/jobs/inbox` | Reviewing automated results |
| Manual paste | `/jobs/postings/new` | Jobs you find on your own |
| URL fetch | `/jobs/postings/fetch` | Jobs with a direct listing URL |
| RSS feeds | `/jobs/discover` | Company career page feeds |

---

## Automated Discovery

### Step 1: Create a search profile

Go to **Jobs → Search Profiles → New** (`/jobs/search-profiles/new`).

Configure:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Profile label | "Senior Backend - Remote" |
| Titles | Target job titles | ["Senior Software Engineer", "Staff Engineer"] |
| Locations | Target locations | ["San Francisco", "Remote"] |
| Remote preference | `any`, `remote`, `hybrid`, `onsite` | `remote` |
| Seniority levels | Target levels | ["senior", "staff", "principal"] |
| Min fit score | Minimum score to show in inbox (0–100) | 50 |
| Salary floor | Minimum salary filter | 150000 |
| Keywords include | Required keywords in JD | ["python", "kubernetes"] |
| Keywords exclude | Excluded keywords | ["intern", "junior"] |
| Sources | Enabled connectors | See sources table below |

### Discovery sources

| Source | Type | Configuration needed |
|--------|------|---------------------|
| `adzuna` | API | `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in `.env` |
| `remotive` | API | None (public API) |
| `greenhouse` | API + optional MyGreenhouse | Company board tokens (e.g. `stripe`) **or** `my` for [MyGreenhouse](https://my.greenhouse.io/jobs?query=) search (requires portal credentials) |
| `lever` | API | Board slugs in search profile (e.g. `["netflix", "dropbox"]`) |
| `rss` | RSS feeds | Feed URLs in search profile |
| `indeed` | Playwright scrape | Portal credentials, `INDEED_SCRAPE_ENABLED=true` |
| `linkedin` | Playwright scrape | Portal credentials, `LINKEDIN_SCRAPE_ENABLED=true` |

API-based sources (Adzuna, Remotive, Greenhouse, Lever, RSS) work without browser automation. Indeed and LinkedIn require portal credentials and administrator setup.

### Step 2: Run discovery

From the search profiles list (`/jobs/search-profiles`):

1. Find your profile
2. Click **Run Discovery** (`POST /jobs/search-profiles/<id>/run`)

**Local dev:** Runs immediately in the Flask process.
**Docker/Celery:** Queued to background worker.

Each connector runs independently. Results are logged in `DiscoveryRun` records.

### Step 3: Review the inbox

Go to **Jobs → Discovery Inbox** (`/jobs/inbox`).

Jobs are sorted by **fit score** (highest first). Each card shows:
- Job title and company
- Location and remote type
- Source connector
- Fit score (0–100)
- Description snippet

**Fit score** measures how well the job matches your active master profile based on keyword overlap, title match, and seniority alignment.

### Step 4: Accept or skip

| Action | Route | Result |
|--------|-------|--------|
| Accept | `POST /jobs/inbox/<id>/accept` | Creates `JobPosting` + `Application` (stage: `saved`) |
| Skip | `POST /jobs/inbox/<id>/skip` | Marks as skipped; removed from inbox |

**Accept** may trigger job detail enrichment for Indeed/LinkedIn listings with thin descriptions (full JD scrape via Playwright).

### Company blocklist

Block companies or URL patterns from appearing in discovery results. Configured per user in the search profile or blocklist settings.

---

## Manual Job Intake

### Paste job details

1. Go to **Jobs → Add Job** (`/jobs/postings/new`)
2. Enter title, company, description, location, URL
3. Save

Source is set to `manual`.

### Fetch from URL

1. Go to **Jobs → Fetch from URL** (`/jobs/postings/fetch`)
2. Paste the job listing URL
3. Click **Fetch**

The app extracts title, company, description, and location from the page. Extraction quality depends on the site structure.

### RSS discovery

1. Go to **Jobs → Discover Jobs** (`/jobs/discover`)
2. Add RSS feed URLs or use preconfigured feeds
3. Browse discovered listings
4. Save interesting jobs as postings

---

## Job Posting Detail

Open any posting at `/jobs/postings/<id>`:

- Full job description and requirements
- Keyword analysis vs your active master profile
  - Matched keywords (green)
  - Missing keywords (red)
  - Coverage score percentage
- Fit score
- Source and URL
- **Create Application** button
- **Refresh Details** — Re-scrape Indeed/LinkedIn for updated description

### Refresh job details

For Indeed/LinkedIn postings, click **Refresh Details** (`POST /jobs/postings/<id>/refresh-details`) to re-scrape the full job description. Useful when the initial listing had a truncated description.

---

## Posting List

**Jobs → Job Postings** (`/jobs/postings`) shows all saved postings:
- Filter by source, company, active status
- Sort by date, fit score, company
- Quick links to detail and create application

---

## Tips

1. **Start with API sources** — Adzuna and Remotive work without credentials
2. **Set a reasonable min fit score** — 50 is a good default; raise to 70 for stricter filtering
3. **Use keywords exclude** — Filter out "intern", "junior", or unwanted technologies
4. **Review inbox regularly** — Discovery runs don't auto-accept; you control what enters your pipeline
5. **Check keyword coverage on posting detail** — Before creating an application, see if the job is a good match
6. **Greenhouse boards** — Use company tokens from career URLs (`boards.greenhouse.io/stripe` → `stripe`). For aggregated search on [MyGreenhouse](https://my.greenhouse.io/jobs?query=), add `my` to the boards list and store a Greenhouse portal session (`python scripts/export_playwright_storage.py greenhouse`). Do not paste the MyGreenhouse URL as a board token.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No jobs in inbox | Check search profile is active; verify source credentials; lower min fit score |
| Indeed/LinkedIn empty | Portal credentials required; ask admin to enable scraping flags |
| Low fit scores | Update master profile skills; broaden search titles |
| Duplicate jobs | Normal — duplicates are filtered automatically; existing postings won't reappear |
| Thin descriptions | Click Refresh Details on posting detail page |

## Related Docs

- [WORKFLOW.md](WORKFLOW.md) — Discovery in the full workflow
- [CONCEPTS.md](CONCEPTS.md) — Search profile and inbox concepts
- [AUTOMATION_SETUP.md](../04-operations/AUTOMATION_SETUP.md) — Configuring scraping (admin)
- [APPLICATIONS.md](APPLICATIONS.md) — Creating applications from postings
