"""Jobs API routes."""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import (
    CompanyBlocklist, DiscoveredJob, DiscoveredJobStatus, JobPosting, JobSearchProfile,
    JobSource, KeywordAnalysis, MasterProfile,
)
from app.services.discovery_orchestrator import discovery_orchestrator
from app.services.job_discovery_service import job_discovery_service
from app.services.keyword_service import keyword_service
from app.utils.security import sanitize_input

logger = logging.getLogger(__name__)

jobs_api_bp = Blueprint('jobs_api', __name__, url_prefix='/api/v1/jobs')


@jobs_api_bp.route('/postings', methods=['GET'])
@login_required
def list_postings():
    postings = JobPosting.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(JobPosting.created_at.desc()).all()
    return jsonify({'data': [p.to_dict() for p in postings]})


@jobs_api_bp.route('/postings', methods=['POST'])
@login_required
def create_posting():
    data = request.get_json() or {}
    title = sanitize_input(data.get('title', '').strip(), 255)
    company = sanitize_input(data.get('company', '').strip(), 255)
    if not title or not company:
        return jsonify({'error': 'Title and company are required'}), 400

    description = data.get('description', '')
    keywords = keyword_service.extract_keywords(description)

    posting = JobPosting(
        user_id=current_user.id,
        title=title,
        company=company,
        description=description,
        requirements=data.get('requirements'),
        location=sanitize_input(data.get('location', ''), 255),
        url=data.get('url'),
        source=data.get('source', JobSource.MANUAL.value),
        seniority=data.get('seniority'),
        extracted_keywords=keywords,
    )
    db.session.add(posting)
    db.session.commit()
    return jsonify(posting.to_dict()), 201


@jobs_api_bp.route('/postings/fetch-url', methods=['POST'])
@login_required
def fetch_from_url():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        job_data = job_discovery_service.fetch_from_url(url)
        return jsonify(job_data)
    except Exception as exc:
        logger.exception('URL fetch failed')
        return jsonify({'error': str(exc)}), 400


@jobs_api_bp.route('/postings/<uuid:posting_id>/keywords', methods=['GET'])
@login_required
def analyze_keywords(posting_id):
    posting = JobPosting.query.filter_by(
        id=posting_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    if not profile:
        return jsonify({'error': 'No active master profile found'}), 400

    jd_text = f"{posting.description or ''} {posting.requirements or ''}"
    analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})

    record = KeywordAnalysis(
        user_id=current_user.id,
        job_posting_id=posting.id,
        master_profile_id=profile.id,
        jd_keywords=analysis['jd_keywords'],
        matched_keywords=analysis['matched_keywords'],
        missing_keywords=analysis['missing_keywords'],
        synonym_matches=analysis['synonym_matches'],
        coverage_score=analysis['coverage_score'],
    )
    db.session.add(record)
    posting.fit_score = job_discovery_service.calculate_fit_score(
        analysis['jd_keywords'], profile.profile_data or {}
    )
    db.session.commit()
    return jsonify({**analysis, 'fit_score': posting.fit_score, 'analysis_id': str(record.id)})


@jobs_api_bp.route('/postings/<uuid:posting_id>', methods=['GET'])
@login_required
def get_posting(posting_id):
    posting = JobPosting.query.filter_by(
        id=posting_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    return jsonify(posting.to_dict())


@jobs_api_bp.route('/postings/<uuid:posting_id>', methods=['PATCH'])
@login_required
def update_posting(posting_id):
    posting = JobPosting.query.filter_by(
        id=posting_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = request.get_json() or {}
    for field in ('title', 'company', 'description', 'requirements', 'location', 'url', 'seniority'):
        if field in data:
            setattr(posting, field, data[field])
    if 'description' in data or 'requirements' in data:
        jd_text = f"{posting.description or ''} {posting.requirements or ''}"
        posting.extracted_keywords = keyword_service.extract_keywords(jd_text)
    db.session.commit()
    return jsonify(posting.to_dict())


@jobs_api_bp.route('/discover/rss', methods=['POST'])
@login_required
def discover_rss():
    data = request.get_json() or {}
    feed_url = data.get('feed_url', '').strip()
    if not feed_url:
        return jsonify({'error': 'feed_url is required'}), 400
    try:
        jobs = job_discovery_service.search_rss_feed(feed_url, limit=data.get('limit', 20))
        return jsonify({'data': jobs})
    except Exception as exc:
        logger.exception('RSS discovery failed')
        return jsonify({'error': str(exc)}), 400


@jobs_api_bp.route('/discover/rss/save', methods=['POST'])
@login_required
def save_rss_jobs():
    data = request.get_json() or {}
    jobs = data.get('jobs') or []
    saved = []
    for job in jobs:
        url = (job.get('url') or '').strip()
        if url and JobPosting.query.filter_by(user_id=current_user.id, url=url, is_deleted=False).first():
            continue
        posting = JobPosting(
            user_id=current_user.id,
            title=sanitize_input(job.get('title', 'Untitled'), 255),
            company=sanitize_input(job.get('company', 'Unknown'), 255),
            description=job.get('description', ''),
            url=url or None,
            source=JobSource.RSS.value,
        )
        db.session.add(posting)
        saved.append(posting)
    db.session.commit()
    return jsonify({'saved': len(saved), 'data': [p.to_dict() for p in saved]}), 201


@jobs_api_bp.route('/search-profiles', methods=['GET'])
@login_required
def list_search_profiles():
    profiles = JobSearchProfile.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(JobSearchProfile.created_at.desc()).all()
    return jsonify({'data': [p.to_dict() for p in profiles]})


@jobs_api_bp.route('/search-profiles', methods=['POST'])
@login_required
def create_search_profile():
    data = request.get_json() or {}
    profile = JobSearchProfile(
        user_id=current_user.id,
        name=sanitize_input(data.get('name', 'Default Search'), 255),
        titles=data.get('titles') or [],
        locations=data.get('locations') or [],
        remote_preference=data.get('remote_preference', 'any'),
        min_fit_score=int(data.get('min_fit_score', 50)),
        sources=data.get('sources') or ['adzuna', 'remotive'],
        greenhouse_boards=data.get('greenhouse_boards') or [],
        lever_boards=data.get('lever_boards') or [],
        rss_feeds=data.get('rss_feeds') or [],
        schedule_hours=int(data.get('schedule_hours', 6)),
        is_active=True,
        indeed_max_age_days=int(data.get('indeed_max_age_days', 7)),
        indeed_radius_miles=int(data.get('indeed_radius_miles', 0)),
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@jobs_api_bp.route('/search-profiles/<uuid:profile_id>', methods=['PATCH'])
@login_required
def update_search_profile(profile_id):
    profile = JobSearchProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    data = request.get_json() or {}
    for field in (
        'titles', 'locations', 'remote_preference', 'min_fit_score', 'sources',
        'greenhouse_boards', 'lever_boards', 'rss_feeds', 'schedule_hours', 'is_active',
        'indeed_max_age_days', 'indeed_radius_miles',
    ):
        if field in data:
            setattr(profile, field, data[field])
    if 'name' in data:
        profile.name = sanitize_input(data['name'], 255)
    db.session.commit()
    return jsonify(profile.to_dict())


@jobs_api_bp.route('/search-profiles/<uuid:profile_id>', methods=['DELETE'])
@login_required
def delete_search_profile(profile_id):
    profile = JobSearchProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile.soft_delete()
    db.session.commit()
    return jsonify({'success': True})


@jobs_api_bp.route('/search-profiles/<uuid:profile_id>/run', methods=['POST'])
@login_required
def run_search_profile(profile_id):
    try:
        discovery_orchestrator.run_discovery(profile_id, current_user.id)
        return jsonify({'success': True})
    except Exception as exc:
        logger.exception('Discovery run failed')
        return jsonify({'error': str(exc)}), 400


@jobs_api_bp.route('/inbox', methods=['GET'])
@login_required
def list_inbox():
    jobs = DiscoveredJob.query.filter_by(
        user_id=current_user.id,
        status=DiscoveredJobStatus.NEW.value,
    ).order_by(DiscoveredJob.fit_score.desc()).limit(100).all()
    return jsonify({'data': [j.to_dict() for j in jobs]})


@jobs_api_bp.route('/inbox/<uuid:discovered_id>/accept', methods=['POST'])
@login_required
def accept_inbox_job(discovered_id):
    try:
        posting = discovery_orchestrator.accept_discovered_job(discovered_id, current_user.id)
    except Exception as exc:
        logger.exception('Accept discovered job failed')
        return jsonify({'success': False, 'error': str(exc)}), 400
    payload = {
        'success': True,
        'posting_id': str(posting.id),
        'discovered_id': str(discovered_id),
    }
    if not (posting.description or '').strip():
        payload['warning'] = (
            'Job accepted, but the full description could not be fetched. '
            'Open the posting and use Refresh Details.'
        )
    else:
        payload['message'] = 'Job accepted and added to postings.'
    return jsonify(payload)


@jobs_api_bp.route('/inbox/<uuid:discovered_id>/skip', methods=['POST'])
@login_required
def skip_inbox_job(discovered_id):
    try:
        discovery_orchestrator.skip_discovered_job(discovered_id, current_user.id)
    except Exception as exc:
        logger.exception('Skip discovered job failed')
        return jsonify({'success': False, 'error': str(exc)}), 400
    return jsonify({'success': True, 'discovered_id': str(discovered_id), 'message': 'Job skipped.'})
