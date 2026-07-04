"""Export Playwright storage_state after manual login (run locally)."""

import json
import os
import platform
import socket
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Home page is more reliable than /login for DNS + redirects.
LOGIN_URLS = {
    'linkedin': 'https://www.linkedin.com/',
    'indeed': 'https://www.indeed.com/',
}

SESSION_COOKIES = {
    'linkedin': ('li_at',),
    'indeed': ('PPID', 'CTK'),
}

VERIFY_URLS = {
    'linkedin': 'https://www.linkedin.com/jobs/',
    'indeed': 'https://www.indeed.com/',
}

BROWSER_ARGS = [
    '--disable-gpu',
    '--disable-gpu-compositing',
    '--disable-accelerated-2d-canvas',
    '--disable-accelerated-video-decode',
]

DNS_ERROR_MARKERS = (
    'dns entry',
    'err_name_not_resolved',
    'server not found',
    'unable to locate the server',
    'nxdomain',
)


def _check_dns(hostname: str) -> bool:
    try:
        socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        return True
    except OSError as exc:
        print(f'DNS lookup failed for {hostname}: {exc}')
        return False


def _default_channel() -> str:
    configured = os.getenv('PLAYWRIGHT_CHANNEL', '').strip()
    if configured:
        return configured
    if platform.system() == 'Darwin':
        return 'chrome'
    return ''


def _launch_browser(playwright, channel: str = ''):
    launch_kwargs = {'headless': False, 'args': BROWSER_ARGS}
    channels_to_try = [channel] if channel else []
    if 'chrome' not in channels_to_try:
        channels_to_try.append('chrome')
    channels_to_try.append('')  # Playwright-bundled Chromium

    last_error = None
    for ch in channels_to_try:
        try:
            if ch:
                print(f'Launching browser (channel={ch})...')
                return playwright.chromium.launch(channel=ch, **launch_kwargs)
            print('Launching Playwright Chromium...')
            return playwright.chromium.launch(**launch_kwargs)
        except Exception as exc:
            last_error = exc
            if ch:
                print(f'Could not launch channel={ch!r}: {exc}')
    raise RuntimeError(f'No browser available: {last_error}')


def _cookie_names(context) -> set:
    return {c.get('name') for c in context.cookies()}


def _has_session_cookie(context, portal: str) -> bool:
    names = _cookie_names(context)
    required = SESSION_COOKIES[portal]
    if portal == 'linkedin':
        return 'li_at' in names
    return any(name in names for name in required)


def _page_has_dns_error(page) -> bool:
    try:
        text = page.content().lower()
    except Exception:
        return False
    return any(marker in text for marker in DNS_ERROR_MARKERS)


def _print_dns_help(portal: str):
    host = 'www.linkedin.com' if portal == 'linkedin' else 'www.indeed.com'
    print('\nBrowser could not resolve the portal hostname.')
    print('Try these fixes:')
    print(f'  1. Open https://{host}/ in your normal Chrome/Safari — confirm it loads')
    print('  2. Re-run with system Chrome: PLAYWRIGHT_CHANNEL=chrome python scripts/export_playwright_storage.py linkedin')
    print('  3. Disable VPN/proxy or add split-tunnel for LinkedIn')
    print('  4. Flush DNS: sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder')
    print('  5. If Playwright Chromium fails, install Google Chrome and use channel=chrome')


def _goto_portal(page, portal: str) -> bool:
    url = LOGIN_URLS[portal]
    print(f'Opening {url} ...')
    try:
        response = page.goto(url, wait_until='domcontentloaded', timeout=90000)
        if response and response.status >= 400:
            print(f'Warning: HTTP {response.status} from {page.url}')
    except Exception as exc:
        print(f'Navigation error: {exc}')
        return False

    if _page_has_dns_error(page):
        _print_dns_help(portal)
        return False
    return True


def _wait_for_login(context, page, portal: str, timeout_sec: int = 600) -> bool:
    print('Complete login in the browser window.')
    print(f'Waiting for session cookies (up to {timeout_sec // 60} minutes). Do not close the browser.')
    start = time.time()
    last_status = 0
    while time.time() - start < timeout_sec:
        if _has_session_cookie(context, portal):
            return True
        elapsed = int(time.time() - start)
        if elapsed - last_status >= 15:
            print(f'  Still waiting ({elapsed}s)... current URL: {page.url}')
            last_status = elapsed
        time.sleep(1)
    return False


def _validate_state(state: dict, portal: str) -> list:
    names = {c.get('name') for c in state.get('cookies', [])}
    return [name for name in SESSION_COOKIES[portal] if name not in names]


def export_session(portal: str, output_path: str):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('Playwright is not installed.')
        print('Install with: pip install -r requirements/requirements-jobs.txt')
        print('Then run: playwright install chromium')
        sys.exit(1)

    if portal not in LOGIN_URLS:
        print(f'Unsupported portal: {portal}. Use: linkedin, indeed')
        sys.exit(1)

    host = 'www.linkedin.com' if portal == 'linkedin' else 'www.indeed.com'
    if not _check_dns(host):
        print(f'\nYour machine cannot resolve {host} before the browser opens.')
        _print_dns_help(portal)
        sys.exit(1)

    playwright = sync_playwright().start()
    browser = None
    exit_code = 0
    try:
        browser = _launch_browser(playwright, channel=_default_channel())
        context = browser.new_context()
        page = context.new_page()

        if not _goto_portal(page, portal):
            exit_code = 1
        elif not _wait_for_login(context, page, portal):
            print('\nERROR: Login timed out — no session cookie detected.')
            print('Finish login in the browser, then run this script again.')
            exit_code = 1
        else:
            verify_url = VERIFY_URLS[portal]
            print(f'Login detected. Opening {verify_url} to finalize session...')
            try:
                page.goto(verify_url, wait_until='domcontentloaded', timeout=90000)
                time.sleep(2)
            except Exception as exc:
                print(f'Warning: verify navigation issue ({exc}); exporting cookies anyway.')

            state = context.storage_state()
            user_agent = page.evaluate('() => navigator.userAgent')
            export_payload = {
                'storage_state': state,
                'user_agent': user_agent,
            }
            missing = _validate_state(state, portal)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_payload, f, indent=2)

            cookie_count = len(state.get('cookies', []))
            print(f'\nSaved storage_state to {output_path} ({cookie_count} cookies).')
            if missing:
                print(f'WARNING: expected cookies not found: {", ".join(missing)}')
                print('The export may not work for discovery — try logging in again.')
                exit_code = 1
            else:
                print(f'Session looks valid ({", ".join(SESSION_COOKIES[portal])} present).')
            print('Paste the full JSON file into Portal Credentials at /apply/credentials')
            print('Closing the browser does NOT invalidate the saved JSON file.')

        input('\nPress Enter to close the browser...')
    finally:
        if browser:
            browser.close()
        playwright.stop()
    sys.exit(exit_code)


if __name__ == '__main__':
    portal = sys.argv[1] if len(sys.argv) > 1 else 'linkedin'
    out = sys.argv[2] if len(sys.argv) > 2 else f'{portal}_storage_state.json'
    export_session(portal, out)
