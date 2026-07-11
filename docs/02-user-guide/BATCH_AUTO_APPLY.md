# Batch Auto-Apply

Submit multiple applications to job portals through automated batch processing.

## Prerequisites

- Applications at stage `ready_to_apply` with approved resumes — see [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md)
- Portal credentials configured — see setup below
- Administrator has enabled auto-apply flags (all disabled by default)

## Important Safety Notes

- **Auto-apply is disabled by default** — An administrator must explicitly enable it
- **You must approve every batch** — Nothing is submitted without your explicit approval
- **Daily cap enforced** — Default maximum 25 applications per day (`DAILY_APPLY_CAP`)
- **Review readiness first** — Each application is checked before submission

## Portal Credentials Setup

Before using batch auto-apply or LinkedIn/Indeed discovery, you need portal session credentials.

### Step 1: Generate encryption key

An administrator sets `CREDENTIAL_ENCRYPTION_KEY` in `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Without this key, credentials won't survive server restarts.

### Step 2: Export browser session

Run locally with a visible browser:

```bash
python scripts/export_playwright_storage.py linkedin
python scripts/export_playwright_storage.py indeed
```

This opens the portal in Chrome, waits for you to log in, and saves session cookies to a JSON file.

### Step 3: Paste credentials

1. Navigate to `/apply/credentials`
2. Select portal type (LinkedIn, Indeed, etc.)
3. Paste the full JSON output from the export script
4. Click **Save**
5. Optionally click **Test** to verify the session is valid

Credentials are encrypted at rest using Fernet encryption.

### Session refresh cadence

Portal sessions expire. Plan to refresh them regularly:

| Portal | Typical refresh | When to re-export |
|--------|-----------------|-------------------|
| LinkedIn | Every 3–7 days | Test Session shows **Re-auth needed**, discovery fails with checkpoint/login errors, or `expires_at` is past |
| Indeed | Weekly or after blocks | Headed scrape blocked, or Test Session fails |

Recommended habit:

1. Before a discovery or batch day, open **Portal Credentials** and click **Test Session**
2. If status is **Re-auth needed** or **Untested**, re-run `export_playwright_storage.py` and replace the credential
3. After a successful test, status shows **Healthy** for about 7 days (`expires_at`)

Emergency stop (no restart): Admin → Settings → **Enable file kill switch**, or create `instance/automation_disabled.flag`.

Env override: set `AUTOMATION_DISABLED=true` and restart — clears only after you unset it and restart again.

## Supported Portals

| Portal | Auto-apply flag | Scrape flag | Notes |
|--------|----------------|-------------|-------|
| Greenhouse | `APPLY_AUTOMATION_ENABLED` | — | API-based |
| Lever | `APPLY_AUTOMATION_ENABLED` | — | API-based |
| LinkedIn | `LINKEDIN_AUTO_APPLY_ENABLED` | `LINKEDIN_SCRAPE_ENABLED` | Playwright; Easy Apply |
| Indeed | `INDEED_AUTO_APPLY_ENABLED` | `INDEED_SCRAPE_ENABLED` | Playwright; headed browser required |
| Generic | — | — | Fallback; marks as needs_manual |

## Create a Batch

### Step 1: Select applications

Go to **Applications → Apply Queue** (`/applications/queue`):

1. Applications at stage `ready_to_apply` are available
2. Check the boxes for applications you want to submit
3. Click **Create Apply Batch**

### Step 2: Review batch

Navigate to `/applications/batches/<id>`:

Each application shows a **readiness checklist**:

| Check | Requirement |
|-------|-------------|
| Tailored resume | Resume version exists with status `approved` |
| Apply draft | Draft exists with form fields populated |
| Stage | Application at `ready_to_apply` |
| Portal support | Adapter available for the job's portal |
| Credentials | Valid portal credentials stored |
| Daily cap | Under `DAILY_APPLY_CAP` for today |

Applications failing checks are flagged. You can still include them but submission may fail or require manual intervention.

### Step 3: Approve batch

1. Review all items and their readiness status
2. Add optional batch notes
3. Click **Approve Batch** (`POST /applications/batches/<id>/approve`)

On approval:
- Batch status → `approved` then `running`
- Celery task `submit_apply_batch` processes each item
- Without Celery: runs synchronously in Flask process

### Step 4: Monitor results

After processing, batch status becomes `completed` or `partial_failure`:

| Item status | Meaning |
|-------------|---------|
| `submitted` | Successfully submitted to portal |
| `needs_manual` | Portal requires manual steps |
| `failed` | Submission error (see error message) |

Each application updates:
- `submission_status` on the application record
- `submission_proof` — Screenshot path if captured
- `submission_error` — Error details if failed
- Stage → `applied` on success

## Batch List

**Applications → Apply Batches** (`/applications/batches`):

- All batches with status, item count, created date
- Click to open batch detail

## Daily Cap

The `DAILY_APPLY_CAP` environment variable (default 25) limits total submissions per day across all batches. The apply queue and batch creation show remaining capacity.

If you hit the cap:
- Batch creation still works but approval will only submit up to the remaining limit
- Resets at midnight (server time)

## Submission Proofs

For Playwright-based submissions, screenshots are saved to `instance/submission_proofs/` as proof of apply assist / submission. View them on the **application detail** page when a proof is attached, or in **Admin → Automation Proofs**.

Scrape/session error screenshots use a separate folder: `instance/scrape_proofs/`.

## When to Use Manual vs Batch

| Use manual submission when | Use batch auto-apply when |
|---------------------------|--------------------------|
| Application requires custom answers | Many similar Easy Apply jobs on LinkedIn |
| You want to personalize heavily | Greenhouse/Lever applications with standard forms |
| Portal is unsupported | You've verified credentials and tested a single submission |
| First time applying to a portal | Processing a large queue of ready applications |

## Tips

1. **Test credentials first** — Use the Test button on the credentials page
2. **Start with one application** — Submit manually first to verify the portal works
3. **Review readiness carefully** — Failed submissions waste daily cap slots
4. **Check proofs** — Verify screenshots match expected submission
5. **Monitor partial failures** — Use **Retry Failed Items** on the batch detail page, or finish manually
6. **Indeed needs headed Chrome** — Ensure `INDEED_PLAYWRIGHT_HEADLESS=false`
7. **Docker uses Redis rate limits** — Compose sets `SCRAPE_USE_REDIS=true` so web and Celery share caps

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Credentials invalid | Re-export session; sessions expire periodically |
| All items failed | Check auto-apply flags enabled; verify credentials |
| needs_manual status | Portal requires steps the adapter can't automate |
| Daily cap reached | Wait until next day or ask admin to raise cap |
| Batch stuck running | Check Celery worker logs; restart worker if needed |

## Related Docs

- [AUTOMATION_SETUP.md](../04-operations/AUTOMATION_SETUP.md) — Administrator setup guide
- [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md) — Getting applications to ready_to_apply
- [WORKFLOW.md](WORKFLOW.md) — Submission in full workflow
- [SCRAPING_AND_AUTOMATION.md](../03-development/SCRAPING_AND_AUTOMATION.md) — Technical details
