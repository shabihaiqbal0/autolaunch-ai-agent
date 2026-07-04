"""
backend/screenshot/capture.py

Screenshot Capture — launches a live project URL headless and takes
professional screenshots at multiple screen sizes (desktop, tablet, mobile).
Uses Playwright, since it handles modern JS-heavy sites (React, Streamlit)
far better than plain requests + BeautifulSoup.

Requires one-time setup:
    pip install playwright
    playwright install chromium
"""

import os
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
except ImportError:
    sync_playwright = None


class CaptureError(Exception):
    """Raised when screenshot capture fails."""
    pass


# name: (width, height) — covers the "multiple screen sizes" requirement
BREAKPOINTS = {
    "desktop": (1440, 900),
}