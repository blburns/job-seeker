"""
Pipeline Service
Application kanban pipeline aggregation.
"""

from typing import Any, Dict, List

from app.models.jobs import Application, ApplicationStage


class PipelineService:
    """Build pipeline data for kanban views."""

    STAGES = [s.value for s in ApplicationStage]

    # Terminal stages that set response timestamps
    TERMINAL_STAGES = {
        ApplicationStage.OFFER.value,
        ApplicationStage.REJECTED.value,
        ApplicationStage.WITHDRAWN.value,
    }

    @classmethod
    def get_pipeline_data(cls, user_id, applications: List[Application] = None) -> Dict[str, Any]:
        if applications is None:
            applications = Application.query.filter_by(
                user_id=user_id, is_deleted=False
            ).all()

        pipeline_data = {}
        for stage in cls.STAGES:
            stage_apps = [a for a in applications if a.stage == stage]
            pipeline_data[stage] = {
                'applications': [cls._app_card(a) for a in stage_apps],
                'count': len(stage_apps),
            }

        total = len(applications)
        applied_count = len([a for a in applications if a.stage not in (
            ApplicationStage.SAVED.value, ApplicationStage.TAILORING.value
        )])
        interview_count = len([a for a in applications if a.stage in (
            ApplicationStage.PHONE_SCREEN.value,
            ApplicationStage.INTERVIEW.value,
            ApplicationStage.OFFER.value,
        )])

        return {
            'stages': pipeline_data,
            'summary': {
                'total': total,
                'applied': applied_count,
                'interviews': interview_count,
                'response_rate': round(interview_count / applied_count * 100, 1) if applied_count else 0,
            },
        }

    @classmethod
    def _app_card(cls, application: Application) -> Dict[str, Any]:
        job = application.job_posting
        return {
            'id': str(application.id),
            'stage': application.stage,
            'job_title': job.title if job else 'Unknown',
            'company': job.company if job else 'Unknown',
            'fit_score': job.fit_score if job else None,
            'keyword_coverage': float(application.keyword_coverage_at_apply or 0),
            'applied_at': application.applied_at.isoformat() if application.applied_at else None,
            'url': job.url if job else None,
        }

    @classmethod
    def update_stage(cls, application: Application, new_stage: str) -> Application:
        from datetime import datetime
        if new_stage not in cls.STAGES:
            raise ValueError(f'Invalid stage: {new_stage}')

        application.stage = new_stage
        if new_stage == ApplicationStage.APPLIED.value and not application.applied_at:
            application.applied_at = datetime.utcnow()
        if new_stage in cls.TERMINAL_STAGES and not application.response_at:
            application.response_at = datetime.utcnow()
        return application


pipeline_service = PipelineService()
