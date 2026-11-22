"""Check shared navigation and responsive styling using only a synthetic DB.

Set BRICK_VISUAL_ARTIFACTS to retain screenshots in a chosen directory.
Requires Playwright; BRICK_BROWSER_CHANNEL may select an installed Edge/Chrome.
"""

from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from tempfile import mkdtemp
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]

from models import RebrickableMinifigs, db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_set_detail_colors import seed_colored_copies  # noqa: E402


def verify_color_workflow(page, origin, first):
    page.goto(origin + first.path)
    black = page.locator('#regular-parts [data-color-name="Black"][data-color-group]')
    red = page.locator('#regular-parts [data-color-name="Red"][data-color-group]')
    amount = black.locator('[name="part_id_90"]')
    red_amount = red.locator(f'[name="part_id_{first.regular}"]')
    expect(black.locator("[data-color-progress]")).to_have_text("1 von 2 vollständig")
    expect(amount.locator("xpath=ancestor::tr")).to_have_attribute(
        "data-quantity-state", "complete"
    )
    assert (
        black.locator(".color-swatch").first.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        == "rgb(5, 19, 29)"
    )
    amount.fill("0")
    expect(amount.locator("xpath=ancestor::tr")).to_have_attribute(
        "data-quantity-state", "missing"
    )
    expect(black.locator("[data-color-progress]")).to_have_text("0 von 2 vollständig")
    black.locator(":scope > summary").click()
    expect(amount).to_be_hidden()
    red_amount.fill("5")
    expect(red_amount.locator("xpath=ancestor::tr")).to_have_attribute(
        "data-quantity-state", "complete"
    )
    page.locator("#save-detail").click()
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "saved")
    assert not black.evaluate("element => element.open")
    expect(amount).to_have_attribute("data-saved", "0")
    page.locator("#part-search").fill("Black")
    expect(amount).to_be_visible()
    expect(red).to_be_hidden()
    page.locator("#part-search").fill("")
    page.locator("#collapse-colors").click()
    expect(amount).to_be_hidden()
    expect(red_amount).to_be_hidden()
    page.locator("#expand-colors").click()
    expect(amount).to_be_visible()
    amount.fill("3")  # exceeds required 2; hidden errors must reopen all parents
    page.locator("#collapse-colors").click()
    page.locator("#regular-parts > summary").click()
    page.locator("#save-detail").click()
    expect(amount).to_be_visible()
    expect(amount).to_be_focused()
    expect(amount).to_have_attribute("aria-invalid", "true")
    amount.fill("2")
    page.locator("#save-detail").click()
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "saved")
    page.locator("#filter-mismatched-parts").check()
    expect(black.locator('[name="part_id_91"]')).to_be_visible()
    expect(amount).to_be_hidden()
    expect(red).to_be_hidden()
    page.reload()
    expect(amount).to_have_value("2")
    expect(red_amount).to_have_value("5")
    print(
        "PASS: swatches, live row/group states, collapse, search, validation, save/reload"
    )


def run():
    app = create_test_app()
    with app.app_context():
        db.create_all()
        first, _ = seed_colored_copies()
        db.session.get(RebrickableMinifigs, "fig-1").name = "Explorer pilot"
        db.session.commit()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    artifacts = Path(os.environ.get("BRICK_VISUAL_ARTIFACTS") or mkdtemp())
    artifacts.mkdir(parents=True, exist_ok=True)
    errors = []
    failed_assets = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel=os.environ.get("BRICK_BROWSER_CHANNEL"), headless=True
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "response",
                lambda response: (
                    failed_assets.append(response.url)
                    if response.url.startswith(origin + "/static/")
                    and response.status >= 400
                    else None
                ),
            )

            # Cache CDN dependencies for repeatable viewport navigation; never
            # contact collection integrations or reuse production browser data.
            @lru_cache(maxsize=32)
            def dependency(url):
                cache = os.environ.get("BRICK_VISUAL_CDN_CACHE")
                if cache:
                    path = Path(cache) / sha256(url.encode()).hexdigest()
                    suffix = url.split("?", 1)[0].rsplit(".", 1)[-1]
                    content_type = {
                        "css": "text/css",
                        "js": "application/javascript",
                        "woff2": "font/woff2",
                        "woff": "font/woff",
                        "ttf": "font/ttf",
                    }[suffix]
                    return path.read_bytes(), content_type
                response = page.request.get(url, timeout=15000)
                assert response.ok, url
                return response.body(), response.headers.get("content-type")

            def resources(route):
                url = route.request.url
                if url.startswith(origin):
                    route.continue_()
                elif url.startswith("https://cdn.jsdelivr.net/") or url.startswith(
                    "https://cdnjs.cloudflare.com/"
                ):
                    body, content_type = dependency(url)
                    route.fulfill(body=body, content_type=content_type)
                else:
                    route.abort()

            page.route("**/*", resources)
            paths = {
                "home": "/",
                "dashboard": "/dashboard",
                "sets": "/set_maintain?box_id=1",
                "detail": first.path,
                "warehouse": "/warehouse",
                "rules": "/warehouse/settings-page",
            }
            for width in (1440, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                for name, path in paths.items():
                    response = page.goto(origin + path)
                    assert response.status == 200, path
                    expect(page.locator(".bm-navbar .navbar-brand")).to_be_visible()
                    expect(
                        page.locator(".bm-navbar .navbar-brand img")
                    ).to_have_js_property("naturalWidth", 96)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth + 1"
                    ), (name, width)
                    if name in {"home", "dashboard", "warehouse"}:
                        expect(
                            page.locator('.bm-navbar [aria-current="page"]')
                        ).to_have_count(1)
                    if width == 390:
                        toggle = page.get_by_role("button", name="Toggle navigation")
                        toggle.click()
                        expect(toggle).to_have_attribute("aria-expanded", "true")
                        expect(page.locator("#navbarNav")).to_have_class(
                            re.compile(r"\bshow\b")
                        )
                        page.locator("#setsDropdown").click()
                        expect(
                            page.get_by_role("link", name="Set Maintenance", exact=True)
                        ).to_be_visible()
                        toggle.click()
                        expect(toggle).to_have_attribute("aria-expanded", "false")
                        expect(page.locator("#navbarNav")).to_be_hidden()
                    page.screenshot(
                        path=str(artifacts / f"{name}-{width}.png"), full_page=True
                    )
                    if name == "detail" and width == 1440:
                        page.locator("#regular-parts").screenshot(
                            path=str(artifacts / "color-groups.png")
                        )
            page.emulate_media(reduced_motion="reduce")
            verify_color_workflow(page, origin, first)
            page.goto(origin + "/")
            page.keyboard.press("Tab")
            assert page.evaluate(
                "getComputedStyle(document.activeElement).outlineStyle !== 'none'"
            )
            assert not errors, errors
            assert not failed_assets, failed_assets
            # Render the native banner as a GitHub-compatible social preview.
            page.set_viewport_size({"width": 1280, "height": 640})
            page.goto(origin + "/static/brand/project-banner.svg")
            page.screenshot(path=str(artifacts / "project-social.png"))
            page.set_viewport_size({"width": 512, "height": 512})
            page.goto(origin + "/static/brick-icon.svg")
            page.evaluate("""() => {
                document.documentElement.setAttribute('width', '512');
                document.documentElement.setAttribute('height', '512');
            }""")
            page.screenshot(
                path=str(artifacts / "project-icon.png"), omit_background=True
            )
            browser.close()
            print(
                f"PASS: 12 page/viewport checks, mobile navigation, focus; {artifacts}"
            )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()


if __name__ == "__main__":
    run()
