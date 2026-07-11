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


BREAKPOINTS = {
    "desktop": (1440, 900),
    "tablet": (768, 1024),
    "mobile": (375, 667),
}


def capture_screenshots(url: str, output_dir: str) -> list[str]:
    """
    Captures screenshots of the given URL at desktop, tablet, and mobile resolutions.
    Saves them inside output_dir.
    Returns:
        list of absolute file paths to the generated screenshots.
    """
    if sync_playwright is None:
        print("Playwright not installed, skipping screenshot capture.")
        return []

    screenshot_paths = []
    try:
        with sync_playwright() as p:
            # Try to launch Chromium; if it fails (e.g. chromium not installed), catch error
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                print(f"Failed to launch browser: {e}. Make sure to run 'playwright install chromium'")
                return []

            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
            except Exception as e:
                # Fallback to load event if networkidle takes too long
                try:
                    page.goto(url, wait_until="load", timeout=10000)
                except Exception as ex:
                    browser.close()
                    raise CaptureError(f"Failed to load URL {url}: {ex}")

            # Give React or other JS frameworks a moment to animate / render
            import time
            time.sleep(2)

            for name, (width, height) in BREAKPOINTS.items():
                page.set_viewport_size({"width": width, "height": height})
                filename = f"screenshot_{name}.png"
                filepath = os.path.join(output_dir, filename)
                page.screenshot(path=filepath, full_page=False)
                screenshot_paths.append(filepath)

            browser.close()
    except Exception as e:
        print(f"Error during screenshot capture: {e}")
        # Don't fail the whole pipeline if screenshots fail

    return screenshot_paths