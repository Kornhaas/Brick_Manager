"""All workspaces, populated states and keyboard/mobile frame, on synthetic data.

Uses cached, unmodified CDN assets when BRICK_VISUAL_CDN_CACHE is supplied.
BRICK_VISUAL_ARTIFACTS selects the screenshot folder. No production app imports.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]

from flask import render_template  # noqa: E402
from models import RebrickableMinifigs, RebrickableParts, RebrickableSets, db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_app_shell import PAGES  # noqa: E402
from brick_manager.tests.test_set_detail_colors import seed_colored_copies  # noqa: E402


def add_visual_states(app):
    image = "/static/brick-icon.svg"
    part = dict(
        part_num="3001",
        name="Brick 2 x 4",
        part_cat_id=1,
        category="Bricks",
        color="Red",
        color_rgb="C91A09",
        quantity=5,
        status="Available",
        is_spare=False,
        location="Shelf A / 1 / 2",
        part_img_url=image,
        cached_img_url=image,
    )

    @app.get("/_visual/search")
    def search():
        return render_template(
            "set_search.html",
            set_info=dict(
                set_num="1000-1",
                name="Explorer and Research",
                year=2024,
                num_parts=7,
                set_img_url=image,
            ),
            parts_info=[part, {**part, "is_spare": True}],
            existing_sets=[],
            minifigs_info=[
                dict(
                    fig_num="fig-1",
                    name="Explorer pilot",
                    quantity=1,
                    location="Shelf A",
                    img_url=image,
                    parts=[part],
                )
            ],
        )

    @app.get("/_visual/locations")
    def locations():
        return render_template(
            "part_location.html",
            categories=[(1, "Bricks")],
            parts=[part],
            selected_category_id=1,
            selected_category_name="Bricks",
            card_state="expanded",
            pagination=dict(count=1, next=None, previous=None),
        )

    @app.get("/_visual/results")
    def results():
        items = [
            dict(
                id=number,
                name="Brick " + number,
                score=0.97,
                img_url=image,
                category_name="Bricks",
                lookup_info=None,
                missing_sets=[
                    dict(
                        part_id=index,
                        user_set_id=1,
                        set_name="Explorer",
                        color_hex="#C91A09",
                        color_name="Red",
                        needed=5,
                        have=1,
                        missing=4,
                    )
                ],
            )
            for index, number in enumerate(("3001", "3020"), start=1)
        ]
        return render_template("results.html", result=dict(items=items))

    @app.get("/_visual/empty")
    def empty():
        return render_template("results.html", result=None)

    @app.get("/_visual/error")
    def error():
        return render_template("error.html", message="A recoverable test error")


def run():
    app = create_test_app()
    artifacts = Path(os.environ.get("BRICK_VISUAL_ARTIFACTS") or mkdtemp())
    artifacts.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="brick-ui-instructions-") as instructions:
        folder = Path(instructions) / "1000-1"
        folder.mkdir()
        (folder / "Explorer.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
        app.config.update(INSTRUCTIONS_FOLDER=instructions, MASTER_LOOKUP={})
        with app.app_context():
            db.create_all()
            seed_colored_copies()
            for part in db.session.query(RebrickableParts):
                part.part_img_url = "/static/brick-icon.svg"
            db.session.get(RebrickableSets, "1000-1").img_url = "/static/brick-icon.svg"
            db.session.get(RebrickableMinifigs, "fig-1").name = "Explorer pilot"
            db.session.commit()
        add_visual_states(app)
        server = make_server("127.0.0.1", 0, app, threaded=True)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        errors = []
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    channel=os.environ.get("BRICK_BROWSER_CHANNEL"), headless=True
                )
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.on(
                    "pageerror",
                    lambda error: errors.append(page.url + " " + error.stack),
                )

                @lru_cache(maxsize=48)
                def dependency(url):
                    cache = os.environ.get("BRICK_VISUAL_CDN_CACHE")
                    if cache:
                        path = Path(cache) / sha256(url.encode()).hexdigest()
                        suffix = url.split("?", 1)[0].rsplit(".", 1)[-1]
                        mime = {
                            "css": "text/css",
                            "js": "application/javascript",
                            "woff2": "font/woff2",
                            "woff": "font/woff",
                            "ttf": "font/ttf",
                        }[suffix]
                        return path.read_bytes(), mime
                    response = page.request.get(url, timeout=15000)
                    assert response.ok, url
                    return response.body(), response.headers.get("content-type")

                def resources(route):
                    url = route.request.url
                    if url.startswith(origin):
                        route.continue_()
                    elif url.startswith(
                        (
                            "https://cdn.jsdelivr.net/",
                            "https://cdnjs.cloudflare.com/",
                            "https://code.jquery.com/",
                            "https://cdn.datatables.net/",
                        )
                    ):
                        body, mime = dependency(url)
                        route.fulfill(body=body, content_type=mime)
                    else:
                        route.abort()

                page.route("**/*", resources)
                paths = [
                    *PAGES,
                    *(
                        "/_visual/" + name
                        for name in ("search", "locations", "results", "empty", "error")
                    ),
                ]
                count = 0
                for width in (1440, 390):
                    page.set_viewport_size({"width": width, "height": 1000})
                    for path in paths:
                        response = page.goto(origin + path)
                        assert response.status == 200, path
                        expect(page.locator(".bm-page-header")).to_have_count(1)
                        expect(page.locator("h1")).to_have_count(1)
                        expect(page.locator("main")).to_have_count(1)
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth + 1"
                        ), (path, width)
                        assert page.evaluate("""() => {
                            const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
                            return ids.length === new Set(ids).size;
                        }"""), path
                        edges = page.locator(".bm-page-header").bounding_box()
                        assert (
                            edges["x"] >= 16
                            and edges["x"] + edges["width"] <= width - 15
                        ), (path, edges)
                        name = path.strip("/").replace("/", "-") or "home"
                        if path == "/_visual/search":
                            action = page.locator(".btn-outline-primary").first
                            action.hover()
                            expect(action).to_have_css("color", "rgb(255, 255, 255)")
                            page.mouse.move(0, 0)
                        for button in page.locator(".btn-primary:visible").all():
                            assert button.evaluate(
                                "e => getComputedStyle(e).color === 'rgb(255, 255, 255)'"
                            ), path
                        page.screenshot(
                            path=str(artifacts / f"{name}-{width}.png"), full_page=True
                        )
                        count += 1
                    # Actual search submissions exercise shared form and result states.
                    page.goto(origin + "/lookup_part")
                    page.locator("#part_id").fill("3001")
                    page.locator("#lookup-button").click()
                    expect(
                        page.get_by_role("heading", name="Part Details", exact=True)
                    ).to_be_visible()
                    page.screenshot(
                        path=str(artifacts / f"lookup-filled-{width}.png"),
                        full_page=True,
                    )
                    page.locator("#part_id").fill("unknown-part")
                    page.locator("#lookup-button").click()
                    expect(
                        page.get_by_role("heading", name="No matching part found")
                    ).to_be_visible()
                    page.goto(origin + "/")
                    page.keyboard.press("Tab")
                    expect(page.locator(".bm-skip")).to_be_focused()
                    page.keyboard.press("Enter")
                    expect(page.locator("#main-content")).to_be_focused()
                    if width == 390:
                        toggle = page.get_by_role("button", name="Toggle navigation")
                        toggle.click()
                        expect(toggle).to_have_attribute("aria-expanded", "true")
                        page.locator("#setsDropdown").click()
                        expect(
                            page.get_by_role("link", name="Set Maintenance", exact=True)
                        ).to_be_visible()
                        toggle.click()
                page.emulate_media(media="print")
                page.goto(origin + "/manual_entry")
                expect(page.locator(".bm-navbar")).to_be_hidden()
                expect(page.locator(".bm-page-header")).to_be_hidden()
                expect(page.locator("#part_num")).to_be_visible()
                assert not errors, errors
                browser.close()
                print(
                    f"PASS: {count} page/viewport checks, filled/unknown lookup, keyboard, mobile nav, print; {artifacts}"
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
