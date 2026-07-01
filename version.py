"""
Version information for Flask Application Boilerplate
Semantic versioning: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes or major architectural changes
- MINOR: New features, phases, or significant additions
- PATCH: Bug fixes, documentation updates, minor improvements

Phase-based versioning:
- v0.1.0: Phase 1 - Core Foundation Infrastructure
- v0.2.0: Phase 2 - Core Services & Infrastructure  
- v0.3.0: Phase 3 - Business Application Modules
- v0.4.0: Phase 4 - Integration Framework
- v0.5.0: Phase 5 - Advanced Features
- v0.6.0: Phase 6 - Security & Compliance
- v0.7.0: Phase 7 - Testing & Quality Assurance
- v0.8.0: Phase 8 - Deployment & Production
- v0.9.0: Phase 9 - Documentation & Training
- v1.0.0: Production Ready Release
"""

__version__ = "0.2.0"
__phase__ = "Phase 2: Core Services & Infrastructure"
__phase_description__ = "API Infrastructure, Communication Services, Caching & Performance"
__phase_status__ = "COMPLETED"
__phase_completion_date__ = "2025-10-19"

# Version metadata
VERSION_INFO = {
    "version": __version__,
    "phase": __phase__,
    "phase_description": __phase_description__,
    "phase_status": __phase_status__,
    "phase_completion_date": __phase_completion_date__,
    "major": 0,
    "minor": 2,
    "patch": 0,
    "is_prerelease": True,
    "is_development": True,
    "is_production_ready": False
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
        "completion_date": __phase_completion_date__
    }

def get_version_info():
    """Get complete version information"""
    return VERSION_INFO.copy()

def is_phase_complete(phase_number):
    """Check if a specific phase is complete"""
    phase_map = {
        1: __phase_status__ == "COMPLETED",
        2: False,  # Phase 2 not started
        3: False,  # Phase 3 not started
        4: False,  # Phase 4 not started
        5: False,  # Phase 5 not started
        6: False,  # Phase 6 not started
        7: False,  # Phase 7 not started
        8: False,  # Phase 8 not started
        9: False,  # Phase 9 not started
    }
    return phase_map.get(phase_number, False)

def get_next_version():
    """Get the next version for the next phase"""
    return "0.2.0"  # Next phase will be v0.2.0

def get_roadmap():
    """Get the complete version roadmap"""
    return {
        "v0.1.0": {
            "phase": "Phase 1: Core Foundation Infrastructure",
            "status": "COMPLETED",
            "description": "Application Architecture, Database Architecture, Authentication & Authorization System"
        },
        "v0.2.0": {
            "phase": "Phase 2: Core Services & Infrastructure", 
            "status": "NEXT",
            "description": "API Infrastructure, Communication Services, Caching & Performance"
        },
        "v0.3.0": {
            "phase": "Phase 3: Business Application Modules",
            "status": "PLANNED",
            "description": "Multi-Tenant Architecture, Core Business Modules, Application Templates"
        },
        "v0.4.0": {
            "phase": "Phase 4: Integration Framework",
            "status": "PLANNED", 
            "description": "External System Integration, Integration Management"
        },
        "v0.5.0": {
            "phase": "Phase 5: Advanced Features",
            "status": "PLANNED",
            "description": "Reporting & Analytics, Workflow Automation"
        },
        "v0.6.0": {
            "phase": "Phase 6: Security & Compliance",
            "status": "PLANNED",
            "description": "Advanced Security, Compliance Features"
        },
        "v0.7.0": {
            "phase": "Phase 7: Testing & Quality Assurance",
            "status": "PLANNED",
            "description": "Comprehensive Testing, Quality Assurance"
        },
        "v0.8.0": {
            "phase": "Phase 8: Deployment & Production",
            "status": "PLANNED",
            "description": "Infrastructure Setup, Production Deployment"
        },
        "v0.9.0": {
            "phase": "Phase 9: Documentation & Training",
            "status": "PLANNED",
            "description": "Comprehensive Documentation, User Guides"
        },
        "v1.0.0": {
            "phase": "Production Ready Release",
            "status": "PLANNED",
            "description": "Complete boilerplate ready for 40+ business applications"
        }
    }
