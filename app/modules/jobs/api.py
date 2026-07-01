"""Jobs API routes."""

import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import JobPosting, JobSource, KeywordAnalysis, MasterProfile
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
