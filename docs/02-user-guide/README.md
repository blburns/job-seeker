# User Guide

End-user documentation for the Job Seeker Automation App. These guides walk you through every feature from first login to tracking your application pipeline.

## Who This Is For

Job seekers who want to:
- Maintain a structured master resume profile
- Discover relevant jobs automatically or add them manually
- Tailor resumes per job with keyword analysis
- Review pre-filled application drafts before submitting
- Track applications through a kanban pipeline

## Guide Index

| Guide | What you'll learn |
|-------|-------------------|
| [CONCEPTS.md](CONCEPTS.md) | Key terms and how the pieces fit together |
| [WORKFLOW.md](WORKFLOW.md) | Full end-to-end workflow from setup to submission |
| [MASTER_PROFILE.md](MASTER_PROFILE.md) | Upload, review, edit, and export your resume |
| [JOB_DISCOVERY.md](JOB_DISCOVERY.md) | Find jobs automatically or add them manually |
| [APPLICATIONS.md](APPLICATIONS.md) | Create applications and manage your pipeline |
| [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md) | Tailor resumes and review apply drafts |
| [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md) | Submit multiple applications via batch automation |
| [ANALYTICS.md](ANALYTICS.md) | Track your job search metrics |

## Quick Start Paths

### First time here?

1. Log in at `/auth/login`
2. Upload your resume at **Resume → Upload Resume** (`/resume/upload`)
3. Review and save your master profile
4. Read [WORKFLOW.md](WORKFLOW.md) for the full process

### Want to find jobs automatically?

1. Create a search profile at **Jobs → Search Profiles** (`/jobs/search-profiles`)
2. Run discovery and review results in **Jobs → Discovery Inbox** (`/jobs/inbox`)
3. See [JOB_DISCOVERY.md](JOB_DISCOVERY.md) for details

### Working on a specific job?

1. Open the job posting at **Jobs → Job Postings** (`/jobs/postings`)
2. Create an application and tailor your resume
3. See [TAILORING_AND_APPLY.md](TAILORING_AND_APPLY.md) for the review process

### Ready to apply to many jobs?

1. Go to **Applications → Apply Queue** (`/applications/queue`)
2. Select applications and create a batch
3. See [BATCH_AUTO_APPLY.md](BATCH_AUTO_APPLY.md) for the approval process

## Navigation

The sidebar organizes features into three sections:

**Job Seeker**
- Overview — Dashboard with stats and quick actions
- Resume — Master profile, upload, create
- Jobs — Postings, discovery, search profiles, inbox
- Applications — List, pipeline, queue, batches
- Analytics — Metrics and funnel

**Management**
- Admin — User and permission management (admin users only)

**Account**
- Profile, settings, security

## Core Philosophy

This app is **human-in-the-loop automation**. It helps you work faster but never submits an application without your explicit review and approval. You always:

1. Review parsed resume data before saving
2. Review tailored resume changes before approving
3. Review pre-filled form fields and cover letter before applying
4. Explicitly approve batches before auto-submission

## Related Docs

- [GETTING_STARTED.md](../01-getting-started/GETTING_STARTED.md) — Installation and setup
- [00-OVERVIEW.md](../00-OVERVIEW.md) — Application overview
- [ADMIN_GUIDE.md](../04-operations/ADMIN_GUIDE.md) — For system administrators
