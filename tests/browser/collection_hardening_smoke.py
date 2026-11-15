"""Dashboard editing with actual DOM/events and disposable collection data."""

import sys
from pathlib import Path
from threading import Thread
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]
from models import User_Parts, UserMinifigurePart, db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_collection_hardening import colliding_parts  # noqa: E402


def run():
    app = create_test_app()
    with app.app_context():
        db.create_all()
        part_id, _ = colliding_parts.__wrapped__()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with (
            patch("routes.dashboard.load_part_lookup", return_value={}),
            sync_playwright() as p,
        ):
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1365, "height": 900})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            # Existing DataTables initialization is outside this test; native edit
            # handling must function independently of its external CDN scripts.
            page.add_init_script("window.$ = () => ({ready: () => {}});")
            page.route(
                "**/*",
                lambda route: (
                    route.continue_()
                    if route.request.url.startswith(origin)
                    else route.fulfill(status=200, body="")
                ),
            )
            page.goto(origin + "/details/missing_minifigure_parts")
            input = page.locator(".update-quantity").first
            expect(input).to_have_attribute("data-part-type", "minifig")
            held = []

            def hold(route):
                held.append(route)

            page.route("**/update_quantity", hold)
            with page.expect_request("**/update_quantity"):
                input.fill("2")
            input.fill("4")
            assert len(held) == 1
            assert (
                held[0].request.post_data_json["changes"][0]["part_type"] == "minifig"
            )
            with page.expect_request("**/update_quantity"):
                held[0].fulfill(response=held[0].fetch())
            expect(input).to_have_value("4")
            held[1].fulfill(response=held[1].fetch())
            expect(page.locator("#feedback")).to_have_attribute("data-state", "saved")
            page.unroute("**/update_quantity", hold)
            page.route(
                "**/update_quantity",
                lambda route: route.fulfill(
                    status=503,
                    content_type="application/json",
                    body='{"error":"simulated"}',
                ),
                times=1,
            )
            input.fill("3")
            expect(page.locator("#feedback")).to_have_attribute("data-state", "error")
            expect(input).to_have_value("3")
            page.locator("#quantity-retry").click()
            expect(page.locator("#feedback")).to_have_attribute("data-state", "saved")
            input.fill("1.9")
            expect(page.locator("#feedback")).to_have_attribute("data-state", "invalid")
            expect(input).to_have_value("1.9")
            input.fill("999")
            expect(page.locator("#feedback")).to_have_attribute("data-state", "saved")
            expect(input).to_have_value("5")
            with app.app_context():
                assert db.session.get(UserMinifigurePart, part_id).have_quantity == 5
                assert db.session.get(User_Parts, part_id).have_quantity == 4
            assert not errors, errors
            browser.close()
            print(
                "PASS: typed colliding identity, serialized latest edits, real network failure/retry, decimal rejection, clamped acknowledgement and unchanged other inventory."
            )
    finally:
        server.shutdown()
        with app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    run()
