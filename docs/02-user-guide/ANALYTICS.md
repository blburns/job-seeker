# Analytics

Track your job search performance with pipeline metrics and source effectiveness.

## Prerequisites

- At least one application created — see [APPLICATIONS.md](APPLICATIONS.md)
- Pipeline stages updated as you progress — see [WORKFLOW.md](WORKFLOW.md)

## Analytics Dashboard

Open **Analytics** (`/analytics/`) for your job search metrics.

## Available Metrics

### Application Funnel

Visual breakdown of applications by stage:

```
Saved → Tailoring → Ready → Applied → Phone Screen → Interview → Offer
```

Shows count at each stage and conversion rates between stages. Helps identify bottlenecks:
- Many in `saved`? Need to tailor more
- Many in `tailoring`? Need to review and approve
- Many in `ready_to_apply`? Need to submit
- Low `applied` → `phone_screen`? May need better targeting

### Response Rate

Percentage of applied applications that received a response (moved past `applied` stage):
- `phone_screen`, `interview`, `offer` count as responses
- `rejected` also counts as a response
- No response = still at `applied` with no stage change

### Source Effectiveness

Which job sources produce the best results:

| Source | Tracked metrics |
|--------|----------------|
| `manual` | Applications created, response rate |
| `adzuna` | Discovered, accepted, applied, responded |
| `remotive` | Same |
| `greenhouse` | Same |
| `lever` | Same |
| `rss` | Same |
| `linkedin` | Same |
| `indeed` | Same |

Compare sources to focus discovery on what works for your profile.

### Keyword Coverage

Average keyword coverage across applications:
- At tailoring time
- At apply time
- Trend over time

Higher coverage correlates with better ATS match scores.

### Time Metrics

- Average time from `saved` to `applied`
- Average time from `applied` to first response
- Applications per week

## API Access

JSON summary available at `/analytics/api/summary`:

```json
{
  "total_applications": 42,
  "by_stage": {
    "saved": 5,
    "tailoring": 3,
    "ready_to_apply": 8,
    "applied": 20,
    "phone_screen": 3,
    "interview": 2,
    "offer": 1
  },
  "response_rate": 0.30,
  "avg_keyword_coverage": 72.5,
  "source_breakdown": {
    "linkedin": {"discovered": 50, "accepted": 15, "applied": 10, "responded": 3},
    "adzuna": {"discovered": 30, "accepted": 8, "applied": 5, "responded": 1}
  }
}
```

## Improving Your Metrics

### Increase funnel velocity

| Bottleneck | Action |
|------------|--------|
| Stuck in `saved` | Run batch tailor from apply queue |
| Stuck in `tailoring` | Review and approve tailored resumes |
| Stuck in `ready_to_apply` | Submit manually or create apply batch |
| Low response rate | Improve keyword coverage; target better-fit jobs |

### Improve source effectiveness

1. Check which sources have highest accept-to-apply ratio
2. Disable low-performing sources in search profiles
3. Raise `min_fit_score` to filter out poor matches
4. Update master profile skills to improve fit scores

### Improve keyword coverage

1. Add missing skills to master profile (legitimately)
2. Use tailoring to rephrase bullets for JD keywords
3. Address remaining gaps in cover letter
4. Target jobs with higher initial coverage scores

## Tips

1. **Update pipeline regularly** — Analytics are only as accurate as your stage data
2. **Mark rejections** — Move to `rejected` stage for accurate response rate
3. **Review weekly** — Track trends over time, not just snapshots
4. **Compare sources monthly** — Adjust search profile sources based on data
5. **Set goals** — e.g. 5 applications/week, 20% response rate

## Related Docs

- [APPLICATIONS.md](APPLICATIONS.md) — Pipeline management
- [WORKFLOW.md](WORKFLOW.md) — Stage definitions
- [JOB_DISCOVERY.md](JOB_DISCOVERY.md) — Configuring discovery sources
- [JOB_SEEKER_API.md](../03-development/JOB_SEEKER_API.md) — Analytics API details
