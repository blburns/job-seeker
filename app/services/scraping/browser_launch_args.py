"""Chromium launch flags shared by all Playwright scraping sessions."""

# Keep GPU and hardware acceleration off for stable headed/headless scraping
# (avoids crashes on macOS/CI and reduces bot-detection surface).
SCRAPE_BROWSER_ARGS = [
    '--disable-gpu',
    '--disable-gpu-compositing',
    '--disable-accelerated-2d-canvas',
    '--disable-accelerated-video-decode',
    '--use-gl=swiftshader',
    '--disable-blink-features=AutomationControlled',
]
