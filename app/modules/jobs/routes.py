"""Jobs web routes."""

import logging

from flask import flash, redirect, render_template, request, url_for
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
from . import jobs_bp

logger = logging.getLogger(__name__)

SEARCH_SOURCES = ['adzuna', 'remotive', 'greenhouse', 'lever', 'rss', 'indeed', 'linkedin']


def _search_profile_from_form(form) -> dict:
    return {
        'name': sanitize_input(form.get('name', 'Default Search'), 255),
        'titles': [t.strip() for t in form.get('titles', '').split(',') if t.strip()],
        'locations': [l.strip() for l in form.get('locations', '').split(',') if l.strip()],
        'remote_preference': form.get('remote_preference', 'any'),
        'min_fit_score': int(form.get('min_fit_score', 50) or 50),
        'sources': [s for s in form.getlist('sources')],
        'greenhouse_boards': [b.strip() for b in form.get('greenhouse_boards', '').split(',') if b.strip()],
        'lever_boards': [b.strip() for b in form.get('lever_boards', '').split(',') if b.strip()],
        'rss_feeds': [f.strip() for f in form.get('rss_feeds', '').split(',') if f.strip()],
        'schedule_hours': int(form.get('schedule_hours', 6) or 6),
        'is_active': form.get('is_active') == 'on',
        'indeed_max_age_days': int(form.get('indeed_max_age_days', 7) or 7),
        'indeed_radius_miles': int(form.get('indeed_radius_miles', 0) or 0),
    }


def _apply_search_profile_fields(profile: JobSearchProfile, fields: dict) -> None:
    profile.name = fields['name']
    profile.titles = fields['titles']
    profile.locations = fields['locations']
    profile.remote_preference = fields['remote_preference']
    profile.min_fit_score = fields['min_fit_score']
    profile.sources = fields['sources']
    profile.greenhouse_boards = fields['greenhouse_boards']
    profile.lever_boards = fields['lever_boards']
    profile.rss_feeds = fields['rss_feeds']
    profile.schedule_hours = fields['schedule_hours']
    profile.is_active = fields['is_active']
    profile.indeed_max_age_days = fields.get('indeed_max_age_days', 7)
    profile.indeed_radius_miles = fields.get('indeed_radius_miles', 0)


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


@jobs_bp.route('/search-profiles')
@login_required
def search_profiles_list():
    profiles = JobSearchProfile.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(JobSearchProfile.created_at.desc()).all()
    return render_template('modules/jobs/search_profiles_list.html', profiles=profiles)


@jobs_bp.route('/search-profiles/new', methods=['GET', 'POST'])
@login_required
def search_profile_new():
    if request.method == 'POST':
        fields = _search_profile_from_form(request.form)
        profile = JobSearchProfile(user_id=current_user.id, **fields)
        db.session.add(profile)
        db.session.commit()
        flash('Search profile created.', 'success')
        return redirect(url_for('jobs.search_profiles_list'))
    return render_template(
        'modules/jobs/search_profile_form.html',
        profile=None,
        sources=SEARCH_SOURCES,
    )


@jobs_bp.route('/search-profiles/<uuid:profile_id>/edit', methods=['GET', 'POST'])
@login_required
def search_profile_edit(profile_id):
    profile = JobSearchProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()

    if request.method == 'POST':
        _apply_search_profile_fields(profile, _search_profile_from_form(request.form))
        db.session.commit()
        flash('Search profile updated.', 'success')
        return redirect(url_for('jobs.search_profiles_list'))

    return render_template(
        'modules/jobs/search_profile_form.html',
        profile=profile,
        sources=SEARCH_SOURCES,
    )


@jobs_bp.route('/search-profiles/<uuid:profile_id>/delete', methods=['POST'])
@login_required
def search_profile_delete(profile_id):
    profile = JobSearchProfile.query.filter_by(
        id=profile_id, user_id=current_user.id, is_deleted=False
    ).first_or_404()
    profile.soft_delete()
    db.session.commit()
    flash('Search profile deleted.', 'success')
    return redirect(url_for('jobs.search_profiles_list'))


@jobs_bp.route('/inbox')
@login_required
def discovery_inbox():
    from app.models.jobs import DiscoveryRun
    jobs = DiscoveredJob.query.filter_by(
        user_id=current_user.id,
        status=DiscoveredJobStatus.NEW.value,
    ).order_by(DiscoveredJob.fit_score.desc(), DiscoveredJob.created_at.desc()).all()
    recent_runs = DiscoveryRun.query.filter_by(
        user_id=current_user.id,
    ).order_by(DiscoveryRun.created_at.desc()).limit(10).all()
    return render_template(
        'modules/jobs/discovery_inbox.html',
        discovered_jobs=jobs,
        recent_runs=recent_runs,
    )


@jobs_bp.route('/inbox/<uuid:discovered_id>/accept', methods=['POST'])
@login_required
def accept_discovered(discovered_id):
    discovery_orchestrator.accept_discovered_job(discovered_id, current_user.id)
    flash('Job accepted and added to postings.', 'success')
    return redirect(url_for('jobs.discovery_inbox'))


@jobs_bp.route('/inbox/<uuid:discovered_id>/skip', methods=['POST'])
@login_required
def skip_discovered(discovered_id):
    discovery_orchestrator.skip_discovered_job(discovered_id, current_user.id)
    flash('Job skipped.', 'info')
    return redirect(url_for('jobs.discovery_inbox'))


@jobs_bp.route('/search-profiles/<uuid:profile_id>/run', methods=['POST'])
@login_required
def run_discovery(profile_id):
    try:
        run = discovery_orchestrator.run_discovery(profile_id, current_user.id)
        if run:
            flash(
                f'Discovery complete: {run.jobs_found or 0} found, '
                f'{run.jobs_new or 0} added to inbox.',
                'success',
            )
        else:
            flash('Discovery run completed.', 'success')
    except Exception as exc:
        flash(f'Discovery failed: {exc}', 'danger')
    return redirect(url_for('jobs.discovery_inbox'))
