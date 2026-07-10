"""Tests for browser page issue detection."""

from app.services.scraping.browser_manager import BrowserManager


class _FakePage:
    def __init__(self, title='', body=''):
        self._title = title
        self._body = body

    def title(self):
        return self._title

    def inner_text(self, _selector):
        return self._body


def test_linkedin_jobs_html_with_recaptcha_script_not_captcha():
    """LinkedIn bundles mention recaptcha in JS — must not false-positive."""
    html = '''
    <html><head><script src="https://www.google.com/recaptcha/api.js"></script></head>
    <body><div class="base-search-card"><span class="base-search-card__title">Engineer</span></div></body>
    </html>
    '''
    page = _FakePage(title='Jobs | LinkedIn', body='Engineer\nSoftware jobs')
    assert BrowserManager.detect_page_issue(page, html, 'https://www.linkedin.com/jobs/search/') is None


def test_security_checkpoint_detected():
    html = '<html><body>Let\'s do a quick security check</body></html>'
    page = _FakePage(title='Security Verification | LinkedIn', body="Let's do a quick security check")
    result = BrowserManager.detect_page_issue(page, html, 'https://www.linkedin.com/checkpoint/challenge/')
    assert result is not None
    assert result.status.value == 'captcha'


def test_indeed_blocked_page_detected():
    page = _FakePage(title='Blocked - Indeed.com', body='Unable to access')
    result = BrowserManager.detect_page_issue(
        page, '<html></html>', 'https://www.indeed.com/jobs?q=python',
    )
    assert result is not None
    assert result.status.value == 'blocked'
    assert 'Indeed blocked' in result.message


def test_mygreenhouse_login_wall_detected():
    html = '<html><body>Enter your email address to continue. Send security code</body></html>'
    page = _FakePage(title='MyGreenhouse', body='Enter your email address to continue. Send security code')
    result = BrowserManager.detect_page_issue(page, html, 'https://my.greenhouse.io/')
    assert result is not None
    assert result.status.value == 'auth_required'


def test_mygreenhouse_jobs_page_not_false_positive():
    body = 'Saved jobs Job alerts Applications Filter by location Sort by relevance'
    page = _FakePage(title='Jobs | MyGreenhouse', body=body)
    result = BrowserManager.detect_page_issue(
        page, f'<html><body>{body}</body></html>', 'https://my.greenhouse.io/jobs?query=software'
    )
    assert result is None
