"""Job search analytics aggregation."""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.models.jobs import Application, ApplicationStage, ApplyBatchItem, DiscoveredJob, JobPosting


class AnalyticsService:
    @classmethod
    def dashboard_data(cls, user_id) -> Dict[str, Any]:
        apps = Application.query.filter_by(user_id=user_id, is_deleted=False).all()
        postings = JobPosting.query.filter_by(user_id=user_id, is_deleted=False).all()
        discovered = DiscoveredJob.query.filter_by(user_id=user_id).count()

        stage_counts = Counter(a.stage for a in apps)
        total = len(apps)
        applied = sum(1 for a in apps if a.stage not in (
            ApplicationStage.SAVED.value, ApplicationStage.TAILORING.value
        ))
        interviews = sum(1 for a in apps if a.stage in (
            ApplicationStage.PHONE_SCREEN.value,
            ApplicationStage.INTERVIEW.value,
            ApplicationStage.OFFER.value,
        ))

        week_ago = datetime.utcnow() - timedelta(days=7)
        apps_this_week = sum(1 for a in apps if a.created_at and a.created_at >= week_ago)

        source_effectiveness = Counter(p.source for p in postings)
        coverage_scores = [
            float(a.keyword_coverage_at_apply)
            for a in apps if a.keyword_coverage_at_apply is not None
        ]
        avg_coverage = round(sum(coverage_scores) / len(coverage_scores), 1) if coverage_scores else 0

        batch_items = ApplyBatchItem.query.join(Application).filter(
            Application.user_id == user_id
        ).all()
        adapter_success = sum(1 for i in batch_items if i.status == 'submitted')
        adapter_failed = sum(1 for i in batch_items if i.status in ('failed', 'needs_manual'))

        funnel = [
            {'stage': stage, 'count': stage_counts.get(stage, 0)}
            for stage in [
                ApplicationStage.SAVED.value,
                ApplicationStage.TAILORING.value,
                ApplicationStage.READY_TO_APPLY.value,
                ApplicationStage.APPLIED.value,
                ApplicationStage.PHONE_SCREEN.value,
                ApplicationStage.INTERVIEW.value,
                ApplicationStage.OFFER.value,
                ApplicationStage.REJECTED.value,
            ]
        ]

        return {
            'total_applications': total,
            'applied_count': applied,
            'interview_count': interviews,
            'response_rate': round(interviews / applied * 100, 1) if applied else 0,
            'applications_this_week': apps_this_week,
            'discovered_jobs': discovered,
            'avg_keyword_coverage': avg_coverage,
            'source_effectiveness': dict(source_effectiveness),
            'adapter_success': adapter_success,
            'adapter_failed': adapter_failed,
            'funnel': funnel,
        }


analytics_service = AnalyticsService()
