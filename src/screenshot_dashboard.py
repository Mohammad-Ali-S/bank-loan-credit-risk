"""Open dashboard/index.html in Edge, report console errors, and save one screenshot per page."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

HTML = Path("dashboard", "index.html").resolve().as_uri()
PAGES = [("p1", "page1_summary.png"), ("p2", "page2_overview.png"), ("p3", "page3_risk.png")]


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HTML)
        page.wait_for_function("window.Plotly !== undefined")
        for pid, name in PAGES:
            page.click(f'nav button[data-p="{pid}"]')
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join("dashboard", name), full_page=True)
            print("saved", name)
        browser.close()
    print("console errors:", errors or "none")


if __name__ == "__main__":
    main()
