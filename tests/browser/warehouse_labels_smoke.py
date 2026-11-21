"""Warehouse image fallback and durable batch reprinting on disposable SQLite."""

import os
import sys
from io import BytesIO
from pathlib import Path
from threading import Thread
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]
from models import PartStorage, RebrickableInventoryParts, StorageLocation, db  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_part_history import catalog_fixture  # noqa: E402


def run():
    app = create_test_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=True)
    with app.app_context():
        db.create_all()
        catalog_fixture()
        for row in RebrickableInventoryParts.query.filter_by(part_num="old").all():
            row.img_url = "/test-brick.png"
        zone = StorageLocation(kind="zone", label="Aktiv")
        db.session.add(zone)
        db.session.flush()
        rack = StorageLocation(kind="rack", label="7", parent_id=zone.id)
        db.session.add(rack)
        db.session.flush()
        db.session.add(StorageLocation(kind="shelf", label="3", parent_id=rack.id))
        db.session.add(
            PartStorage(
                part_num="old", location="7", level="3", box="2", label_printed=True
            )
        )
        db.session.commit()
    image = Image.new("RGB", (16, 16), "red")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    server = make_server("127.0.0.1", 0, app, threaded=True)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with (
            patch("services.label_service.download_image", return_value=image),
            sync_playwright() as p,
        ):
            browser = p.chromium.launch(
                headless=True, channel=os.environ.get("BRICK_BROWSER_CHANNEL")
            )
            page = browser.new_page(viewport={"width": 1365, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.add_init_script("window.bootstrap={Modal:class {show(){} hide(){}}};")

            def route_request(route):
                if route.request.url.endswith("/test-brick.png"):
                    route.fulfill(
                        status=200, content_type="image/png", body=buffer.getvalue()
                    )
                elif route.request.url.startswith(origin):
                    route.continue_()
                else:
                    route.fulfill(status=200, body="")

            page.route("**/*", route_request)
            page.goto(origin + "/warehouse")
            card = page.locator(".warehouse-legacy-card").first
            expect(card).to_contain_text("Old Bricks")
            preview = card.locator("img").first
            expect(preview).to_be_visible()
            page.wait_for_function(
                "document.querySelector('.warehouse-part-preview img').naturalWidth > 0"
            )
            expect(card.locator(".warehouse-part-icon").first).to_be_hidden()
            card.click()
            detail_image = page.locator("#warehouse-details tbody img").first
            expect(detail_image).to_be_visible()
            page.wait_for_function(
                "document.querySelector('#warehouse-details tbody img').naturalWidth > 0"
            )
            expect(page.locator("#warehouse-details")).to_contain_text("Old Bricks")
            expect(page.locator("#warehouse-details")).to_contain_text("old")
            check = page.locator(".warehouse-card-slot input[type=checkbox]").first
            check.check()
            expect(page.locator("#warehouse-status")).to_contain_text("1 Boxen")
            page.reload()
            expect(
                page.locator(".warehouse-card-slot input[type=checkbox]").first
            ).to_be_checked()
            page.get_by_role("link", name="Boxetiketten drucken").click()
            expect(page.locator("#marked-label-list")).to_contain_text(
                "Schrank 7 / Fach 3 / Box 2"
            )
            page.route(
                "**/warehouse/label-marks/sheet",
                lambda route: route.fulfill(
                    status=500,
                    content_type="application/json",
                    body='{"error":"Simulierter Druckfehler"}',
                ),
                times=1,
            )
            page.locator("#marked-label-download").click()
            expect(page.locator("#marked-label-status")).to_contain_text(
                "Simulierter Druckfehler"
            )
            expect(page.locator("#marked-label-confirm")).to_be_disabled()
            with page.expect_download() as downloaded:
                page.locator("#marked-label-download").click()
            assert Path(downloaded.value.path()).read_bytes().startswith(b"%PDF")
            expect(page.locator("#marked-label-confirm")).to_be_enabled()
            page.reload()
            expect(page.locator("#marked-label-list li")).to_have_count(1)
            expect(page.locator("#marked-label-confirm")).to_be_disabled()
            with page.expect_download():
                page.locator("#marked-label-download").click()
            page.on("dialog", lambda dialog: dialog.accept())
            page.locator("#marked-label-confirm").click()
            expect(page.locator("#marked-label-list li")).to_have_count(0)
            page.goto(origin + "/warehouse")
            expect(
                page.locator(".warehouse-card-slot input[type=checkbox]").first
            ).not_to_be_checked()
            assert not errors, errors
            browser.close()
            print(
                "PASS: inventory image rendered; mark persists across pages/reload; failed PDF keeps mark; real PDF generated; download leaves mark; confirmation clears mark; no JavaScript errors."
            )
    finally:
        server.shutdown()
        with app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    run()
