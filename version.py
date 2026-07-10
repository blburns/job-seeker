"""
Version information for Job Seeker Automation App
Semantic versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes or major architectural changes
- MINOR: New features, phases, or significant additions
- PATCH: Bug fixes, documentation updates, minor improvements

Phase-based versioning (see ROADMAP.md):
- v0.1.0: Phase 1 - Platform Foundation
- v0.2.0: Phase 2 - Core Services & Infrastructure
- v0.3.0: Phase 3 - Job Seeker Core
- v0.4.0: Phase 4 - Automation Hardening
- v0.5.0: Phase 5 - Quality and CI
- v0.6.0: Phase 6 - Security Hardening
- v0.7.0: Phase 7 - Operations and Data
- v0.8.0: Phase 8 - UX, Performance, and Polish
- v0.9.0: Phase 9 - Release Candidate
- v1.0.0: Production Ready Release
"""

__version__ = "0.3.0"
__phase__ = "Phase 4: Automation Hardening"
__phase_description__ = (
    "Playwright scraping reliability, apply adapters that can submit, "
    "and portal credential health"
)
__phase_status__ = "IN_PROGRESS"
__phase_completion_date__ = None
__last_completed_phase__ = "Phase 3: Job Seeker Core"
__last_completed_version__ = "0.3.0"
__last_completed_date__ = "2026-07-10"

# Version metadata
VERSION_INFO = {
    "version": __version__,
    "phase": __phase__,
    "phase_description": __phase_description__,
    "phase_status": __phase_status__,
    "phase_completion_date": __phase_completion_date__,
    "last_completed_phase": __last_completed_phase__,
    "last_completed_version": __last_completed_version__,
    "last_completed_date": __last_completed_date__,
    "major": 0,
    "minor": 3,
    "patch": 0,
    "is_prerelease": True,
    "is_development": True,
    "is_production_ready": False,
}


def get_version():
    """Get the current version string"""
    return __version__


def get_phase_info():
    """Get current phase information"""
    return {
        "phase": __phase__,
        "description": __phase_description__,
        "status": __phase_status__,
        "completion_date": __phase_completion_date__,
        "last_completed_phase": __last_completed_phase__,
        "last_completed_version": __last_completed_version__,
        "last_completed_date": __last_completed_date__,
    }


def get_version_info():
    """Get complete version information"""
    return VERSION_INFO.copy()


def is_phase_complete(phase_number):
    """Check if a specific phase is complete"""
    # Phases 1–3 complete; Phase 4+ not yet exited
    completed = {1, 2, 3}
    return phase_number in completed


def get_next_version():
    """Get the next version for the next completed phase"""
    return "0.4.0"


def get_roadmap():
    """Get the complete version roadmap (mirrors ROADMAP.md)"""
    return {
        "v0.1.0": {
            "phase": "Phase 1: Platform Foundation",
            "status": "COMPLETED",
            "description": (
                "Application factory, auth, RBAC, OAuth, 2FA, Vuexy UI shell"
            ),
        },
        "v0.2.0": {
            "phase": "Phase 2: Core Services & Infrastructure",
            "status": "COMPLETED",
            "description": (
                "API framework, email, Redis, Celery, Docker Compose, health checks"
            ),
        },
        "v0.3.0": {
            "phase": "Phase 3: Job Seeker Core",
            "status": "COMPLETED",
            "description": (
                "Master profile, discovery, tailoring, apply drafts, pipeline, analytics"
            ),
        },
        "v0.4.0": {
            "phase": "Phase 4: Automation Hardening",
            "status": "IN_PROGRESS",
            "description": (
                "Playwright scraping, apply adapters that submit, credentials health"
            ),
        },
        "v0.5.0": {
            "phase": "Phase 5: Quality and CI",
            "status": "PLANNED",
            "description": (
                "GitHub Actions, integration tests, coverage, accurate API docs"
            ),
        },
        "v0.6.0": {
            "phase": "Phase 6: Security Hardening",
            "status": "PLANNED",
            "description": (
                "Secret validation, OAuth encryption, RBAC for job seeker routes"
            ),
        },
        "v0.7.0": {
            "phase": "Phase 7: Operations and Data",
            "status": "PLANNED",
            "description": (
                "Alembic migrations, backups, production Docker, runbooks"
            ),
        },
        "v0.8.0": {
            "phase": "Phase 8: UX, Performance, and Polish",
            "status": "PLANNED",
            "description": (
                "Onboarding, mobile, pagination, notifications, follow-ups"
            ),
        },
        "v0.9.0": {
            "phase": "Phase 9: Release Candidate",
            "status": "PLANNED",
            "description": (
                "Feature freeze, staging soak, CHANGELOG, known limitations"
            ),
        },
        "v1.0.0": {
            "phase": "Production Ready Release",
            "status": "PLANNED",
            "description": (
                "Stable self-hosted release for manual workflow with optional automation"
            ),
        },
    }
