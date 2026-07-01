"""Jobs web routes."""

import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions.core import db
from app.models.jobs import JobPosting, JobSource, KeywordAnalysis, MasterProfile
from app.services.job_discovery_service import job_discovery_service
from app.services.keyword_service import keyword_service
from app.utils.security import sanitize_input
from . import jobs_bp

logger = logging.getLogger(__name__)


@jobs_bp.route('/')
@login_required
def index():
    return redirect(url_for('jobs.postings_list'))


@jobs_bp.route('/postings')
@login_required
def postings_list():
    postings = JobPosting.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(JobPosting.created_at.desc()).all()
    return render_template('modules/jobs/postings_list.html', postings=postings)


@jobs_bp.route('/postings/new', methods=['GET', 'POST'])
@login_required
def posting_new():
    if request.method == 'POST':
        title = sanitize_input(request.form.get('title', '').strip(), 255)
        company = sanitize_input(request.form.get('company', '').strip(), 255)
        description = request.form.get('description', '').strip()
        if not title or not company:
            flash('Title and company are required.', 'warning')
            return render_template('modules/jobs/posting_form.html')

        keywords = keyword_service.extract_keywords(description)
        posting = JobPosting(
            user_id=current_user.id,
            title=title,
            company=company,
            description=description,
            requirements=request.form.get('requirements', '').strip(),
            location=sanitize_input(request.form.get('location', ''), 255),
            url=request.form.get('url', '').strip(),
            source=JobSource.MANUAL.value,
            extracted_keywords=keywords,
        )
        db.session.add(posting)
        db.session.commit()
        flash('Job posting saved.', 'success')
        return redirect(url_for('jobs.posting_detail', posting_id=posting.id))

    return render_template('modules/jobs/posting_form.html')


@jobs_bp.route('/postings/fetch', methods=['GET', 'POST'])
@login_required
def posting_fetch():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if not url:
            flash('URL is required.', 'warning')
            return render_template('modules/jobs/posting_fetch.html')
        try:
            job_data = job_discovery_service.fetch_from_url(url)
            return render_template('modules/jobs/posting_form.html', job_data=job_data)
        except Exception as exc:
            flash(f'Failed to fetch job: {exc}', 'danger')
    return render_template('modules/jobs/posting_fetch.html')


@jobs_bp.route('/postings/<uuid:posting_id>')
@login_required
def posting_detail(posting_id):
    posting = JobPosting.query.filter_by(
        id=posting_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile = MasterProfile.query.filter_by(
        user_id=current_user.id, is_active=True, is_deleted=False
    ).first()
    analysis = None
    if profile:
        jd_text = f"{posting.description or ''} {posting.requirements or ''}"
        analysis = keyword_service.analyze_coverage(jd_text, profile.profile_data or {})
    latest_analysis = KeywordAnalysis.query.filter_by(
        job_posting_id=posting.id, user_id=current_user.id
    ).order_by(KeywordAnalysis.created_at.desc()).first()
    return render_template(
        'modules/jobs/posting_detail.html',
        posting=posting,
        analysis=analysis,
        latest_analysis=latest_analysis,
        profile=profile,
    )


@jobs_bp.route('/discover')
@login_required
def discover():
    return render_template('modules/jobs/discover.html')
