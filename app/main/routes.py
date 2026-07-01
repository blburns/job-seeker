"""
Main Application Routes
Core application routes (index, simple dashboard)
"""

import logging
import uuid
from flask import Blueprint
from flask import render_template
from flask import current_app
from flask import send_from_directory
from flask import abort
from flask import url_for
from flask import request
from flask import flash
from flask import redirect
from flask import jsonify
from flask_login import login_user, logout_user, login_required, current_user
from pathlib import Path

# Import forms (when implemented)
# from app.modules.contact.forms import DefaultContactForm, ScheduleContactForm

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


# User loader will be set up in the app initialization


def get_logo_urls():
    """Get logo URLs for different themes"""
    return {
        'logo_default': url_for('static', filename='images/logo.png')
        # 'logo_light': url_for('static', filename='images/logos/dreamlike-logo-blue-256x256-trans.png'),
        # 'logo_dark': url_for('static', filename='images/logos/dreamlike-logo-red-256x256-trans.png')
    }


@main_bp.route('/health')
def health():
    """Health check - always returns 200, no auth required."""
    return jsonify({'status': 'ok'}), 200


@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Job seeker overview dashboard."""
    from app.models.jobs import Application, JobPosting, MasterProfile
    from app.services.pipeline_service import pipeline_service

    profiles = MasterProfile.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(MasterProfile.created_at.desc()).all()
    active_profile = next((p for p in profiles if p.is_active), None)

    postings = JobPosting.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(JobPosting.created_at.desc()).all()

    applications = Application.query.filter_by(
        user_id=current_user.id, is_deleted=False
    ).order_by(Application.updated_at.desc()).all()
    pipeline = pipeline_service.get_pipeline_data(current_user.id, applications)

    return render_template(
        'main/home.html',
        title='Overview',
        profiles=profiles,
        active_profile=active_profile,
        postings=postings,
        applications=applications,
        pipeline=pipeline,
        **get_logo_urls(),
    )




# @main_bp.route('/docs')
# def docs():
#     """Documentation page"""
#     logos = get_logo_urls()
#     return render_template('main/docs.html', title='Documentation', **logos)


# @main_bp.route('/about')
# def about():
#     """About page"""
#     logos = get_logo_urls()
#     return render_template('main/about.html', title='About', **logos)


# @main_bp.route('/login')
# def login():
#     """Simple login page for testing"""
#     from app.main.models import User
#     from flask_login import login_user
    
#     # Create and login dummy user for testing
#     dummy_user = User()
#     dummy_user.user_uuid = str(uuid.uuid4())
#     dummy_user.email = 'demo@example.com'
#     dummy_user.first_name = 'Demo'
#     dummy_user.last_name = 'User'
#     dummy_user.is_active = True
#     dummy_user.is_admin = False
    
#     login_user(dummy_user)
#     flash('🎉 Welcome! You\'re now logged in and ready to get started!', 'success')
#     flash('💡 Pro tip: Check out the documentation to learn more about the features.', 'info')
#     return redirect(url_for('main.index'))


# @main_bp.route('/logout')
# def logout():
#     """Logout route"""
#     logout_user()
#     flash('You have been logged out', 'info')
#     return redirect(url_for('main.index'))


# # @main_bp.route('/color-test')
# # def color_test():
# #     """Color system test page"""
# #     form = ContactForm()
# #     return render_template(
# #         'pages/color_test.html', 
# #         title='Color System Test', 
# #         form=form
# #     )


# @main_bp.route('/services')
# def services():
#     """Services page"""
#     logos = get_logo_urls()
#     return render_template('pages/services.html', **logos)


# @main_bp.route('/schedule')
# def schedule():
#     """Schedule page"""
#     form = ScheduleContactForm()
#     logos = get_logo_urls()
#     return render_template(
#         'pages/schedule.html', 
#         title='Schedule a Call', 
#         form=form,
#         **logos
#     )


# @main_bp.route('/terms-of-service')
# def terms_and_services():
#     logos = get_logo_urls()
#     return render_template('pages/tos.html', **logos)


# @main_bp.route('/privacy-policy')
# def privacy_policy():
#     """Privacy Policy page"""
#     logos = get_logo_urls()
#     return render_template('pages/privacy.html', **logos)





@main_bp.route('/favicon.ico')
def favicon():
    """Serve the favicon.ico from the generated icons directory.

    Looks under app/static/icons/favicon.ico; falls back to 
    app/static/favicon.ico if present.
    """
    try:
        root = Path(current_app.root_path)
        icons_dir = root / 'static' / 'icons'
        ico_path = icons_dir / 'favicon.ico'
        if ico_path.exists():
            return send_from_directory(str(icons_dir), 'favicon.ico')
        # Fallbacks
        legacy_dir = root / 'static'
        if (legacy_dir / 'favicon.ico').exists():
            return send_from_directory(str(legacy_dir), 'favicon.ico')
    except Exception:
        pass
    abort(404)


@main_bp.route('/site.webmanifest')
def webmanifest():
    """Serve a simple web manifest referencing generated icons if present."""
    try:
        root = Path(current_app.root_path)
        icons_dir = root / 'static' / 'icons'
        if not icons_dir.exists():
            abort(404)
        app_name = current_app.config.get('APP_NAME') or 'App'
        return current_app.response_class(
            response=(
                '{\n'
                '  "name": "' + app_name + '",\n'
                '  "short_name": "' + app_name + '",\n'
                '  "icons": [\n'
                '    { "src": "/static/icons/android-chrome-192x192.png", '
                '"sizes": "192x192", "type": "image/png" },\n'
                '    { "src": "/static/icons/android-chrome-512x512.png", '
                '"sizes": "512x512", "type": "image/png" }\n'
                '  ],\n'
                '  "theme_color": "#111827",\n'
                '  "background_color": "#ffffff",\n'
                '  "display": "standalone"\n'
                '}\n'
            ),
            mimetype='application/manifest+json'
        )
    except Exception:
        abort(404)


@main_bp.route('/error/400')
def error_400():
    """Test endpoint for 400 Bad Request error page"""
    return render_template('errors/400.html'), 400


@main_bp.route('/error/401')
def error_401():
    """Test endpoint for 401 Unauthorized error page"""
    return render_template('errors/401.html'), 401


@main_bp.route('/error/403')
def error_403():
    """Test endpoint for 403 Forbidden error page"""
    return render_template('errors/403.html'), 403


@main_bp.route('/error/404')
def error_404():
    """Test endpoint for 404 Not Found error page"""
    return render_template('errors/404.html'), 404


@main_bp.route('/error/405')
def error_405():
    """Test endpoint for 405 Method Not Allowed error page"""
    return render_template('errors/405.html'), 405


@main_bp.route('/error/408')
def error_408():
    """Test endpoint for 408 Request Timeout error page"""
    return render_template('errors/408.html'), 408


@main_bp.route('/error/500')
def error_500():
    """Test endpoint for 500 Internal Server Error error page"""
    return render_template('errors/500.html'), 500


@main_bp.route('/error/418')
def error_418():
    """Test endpoint for 418 I'm a Teapot error page"""
    return render_template('errors/418.html'), 418


@main_bp.route('/test-errors')
def test_errors():
    """Test page showing links to all error pages for easy testing"""
    return render_template('pages/test_errors.html')




# Common routes to reduce 404 noise
@main_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt to reduce 404 noise from crawlers"""
    robots_content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /error/
Disallow: /test-errors

Sitemap: https://dreamlikelabs.com/sitemap.xml"""
    return current_app.response_class(robots_content, mimetype='text/plain')


@main_bp.route('/sitemap.xml')
def sitemap_xml():
    """Serve a basic sitemap to reduce 404 noise"""
    sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://dreamlikelabs.com/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://dreamlikelabs.com/about</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://dreamlikelabs.com/services</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://dreamlikelabs.com/contact</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://dreamlikelabs.com/terms-of-service</loc>
        <changefreq>yearly</changefreq>
        <priority>0.3</priority>
    </url>
    <url>
        <loc>https://dreamlikelabs.com/privacy-policy</loc>
        <changefreq>yearly</changefreq>
        <priority>0.3</priority>
    </url>
</urlset>"""
    return current_app.response_class(sitemap_content, mimetype='application/xml')


@main_bp.route('/apple-touch-icon.png')
@main_bp.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon():
    """Serve Apple touch icon to reduce 404 noise"""
    try:
        root = Path(current_app.root_path)
        icons_dir = root / 'static' / 'icons'
        icon_path = icons_dir / 'apple-touch-icon.png'
        if icon_path.exists():
            return send_from_directory(str(icons_dir), 'apple-touch-icon.png')
        # Fallback to any available icon
        for icon_file in icons_dir.glob('*.png'):
            if '192' in icon_file.name or '512' in icon_file.name:
                return send_from_directory(str(icons_dir), icon_file.name)
    except Exception:
        pass
    abort(404)


@main_bp.route('/browserconfig.xml')
def browserconfig_xml():
    """Serve browserconfig.xml for Windows tiles to reduce 404 noise"""
    browserconfig_content = """<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
    <msapplication>
        <tile>
            <square150x150logo src="/static/icons/mstile-150x150.png"/>
            <TileColor>#111827</TileColor>
        </tile>
    </msapplication>
</browserconfig>"""
    return current_app.response_class(browserconfig_content, mimetype='application/xml')


@main_bp.route('/.well-known/security.txt')
def security_txt():
    """Serve security.txt to reduce 404 noise from security researchers"""
    security_content = """Contact: mailto:security@dreamlikelabs.com
Expires: 2025-12-31T23:59:59.000Z
Preferred-Languages: en
Canonical: https://dreamlikelabs.com/.well-known/security.txt"""
    return current_app.response_class(security_content, mimetype='text/plain')


@main_bp.route('/.well-known/robots.txt')
def well_known_robots():
    """Redirect .well-known/robots.txt to main robots.txt"""
    return current_app.response_class("""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /error/
Disallow: /test-errors

Sitemap: https://dreamlikelabs.com/sitemap.xml""", mimetype='text/plain')


@main_bp.route('/humans.txt')
def humans_txt():
    """Serve humans.txt to reduce 404 noise"""
    humans_content = """/* TEAM */
    Developer: DreamlikeLabs Team
    Contact: hello@dreamlikelabs.com
    From: United States

/* SITE */
    Last update: 2024
    Language: English
    Doctype: HTML5
    IDE: VS Code
    Standards: HTML5, CSS3, JavaScript
    Components: Flask, Python
    Software: Python 3.11+, Flask 3.0+"""
    return current_app.response_class(humans_content, mimetype='text/plain')
