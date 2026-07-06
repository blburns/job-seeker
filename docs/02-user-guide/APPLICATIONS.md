# Applications

Create, track, and manage job applications through the pipeline.

## Prerequisites

- At least one job posting — see [JOB_DISCOVERY.md](JOB_DISCOVERY.md)
- Active master profile — see [MASTER_PROFILE.md](MASTER_PROFILE.md)

## Create an Application

### From a job posting

1. Open posting detail at `/jobs/postings/<id>`
2. Click **Create Application**
3. Or navigate to `/applications/new?job_id=<posting_id>`

### From discovery accept

Accepting a job in the discovery inbox automatically creates both a posting and an application (stage: `saved`).

### Manual creation

1. Go to **Applications → New Application** (`/applications/new`)
2. Select a job posting
3. Save

New applications start at stage `saved`.

## Application Detail

Open any application at `/applications/<id>`:

### Header
- Job title and company (linked to posting)
- Current stage badge
- Applied date (if submitted)

### Actions
| Button | When available | Action |
|--------|---------------|--------|
| Tailor Resume | Stage is `saved` or `tailoring` | Runs tailoring |
| Review Tailoring | Stage is `tailoring` | Opens tailoring review page |
| Approve Resume | Tailored version pending | Approves and moves to `ready_to_apply` |
| Review & Apply | Stage is `ready_to_apply` | Opens apply draft review |
| Add Notes | Always | Save notes on the application |

### Activity timeline

Chronological log of events:
- Application created
- Resume tailored
- Resume approved
- Apply draft saved
- Marked as applied
- Notes added
- Stage changes

### Notes

Add free-text notes at any time (`POST /applications/<id>/notes`). Useful for tracking recruiter conversations, interview prep, or follow-up reminders.

## Application List

**Applications → All Applications** (`/applications/list`):

Table view with columns:
- Job title and company
- Stage
- Fit score
- Keyword coverage
- Created date
- Applied date

Filter and sort by stage, company, or date.

## Application Dashboard

**Applications** (`/applications/dashboard`) shows:
- Count by stage
- Recent activity
- Quick links to pipeline and queue

## Pipeline Kanban

**Applications → Pipeline** (`/applications/pipeline`):

Visual kanban board with columns for each stage:

```
Saved | Tailoring | Ready to Apply | Applied | Phone Screen | Interview | Offer
```

### Using the board

1. Cards show job title, company, and key metrics
2. **Drag cards** between columns to update stage
3. Stage updates via API (`PATCH /api/v1/applications/<id>/stage`)
4. Click a card to open application detail

### Stage colors

Each column is color-coded for quick visual scanning. Cards in `rejected` and `withdrawn` can be filtered or hidden.

## Apply Queue

**Applications → Apply Queue** (`/applications/queue`):

Lists applications ready for action:
- Stage `saved` or `tailoring` — need tailoring
- Stage `ready_to_apply` — ready for submission

### Batch actions from queue

Select multiple applications to:
- **Batch tailor** — Run tailoring on all selected (background task)
- **Create apply batch** — Group for automated submission

See [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md) for batch details.

## Application Stages Reference

| Stage | Entry trigger | Exit trigger |
|-------|----------------|--------------|
| `saved` | Application created | User clicks Tailor |
| `tailoring` | Tailoring started | User approves resume |
| `ready_to_apply` | Resume approved | User submits (manual or batch) |
| `applied` | Marked as applied | Manual pipeline update |
| `phone_screen` | Manual pipeline update | Manual pipeline update |
| `interview` | Manual pipeline update | Manual pipeline update |
| `offer` | Manual pipeline update | — |
| `rejected` | Manual pipeline update | — |
| `withdrawn` | Manual pipeline update | — |

Stages after `applied` are updated manually via the pipeline board as you hear back from employers.

## Custom Fields

Applications support optional `custom_fields` JSON for tracking data specific to your workflow (e.g. referral contact, application ID on employer site).

## Tips

1. **One application per job** — Avoid duplicate applications for the same posting
2. **Use notes liberally** — Track recruiter names, interview dates, feedback
3. **Update pipeline promptly** — Accurate stages improve analytics
4. **Check queue regularly** — Batch actions save time on multiple applications
5. **Review activity timeline** — Audit trail of all actions on each application

## Related Docs

- [WORKFLOW.md](WORKFLOW.md) — Full application lifecycle
- [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md) — Tailoring and apply review
- [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md) — Batch submission
- [ANALYTICS.md](ANALYTICS.md) — Pipeline metrics
