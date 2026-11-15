"""Real-browser legacy warehouse regression; disposable SQLite only.

Run with the same Playwright environment as warehouse_smoke.py.
"""

import sys
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]
from models import PartStorage, StorageLocation, db  # noqa: E402
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
        zone = StorageLocation(kind="zone", label="Aktiv")
        db.session.add(zone)
        db.session.flush()
        rack = StorageLocation(kind="rack", label="7", parent_id=zone.id)
        db.session.add(rack)
        db.session.flush()
        shelf = StorageLocation(kind="shelf", label="3", parent_id=rack.id)
        db.session.add(shelf)
        db.session.flush()
        shelf_id = shelf.id
        db.session.add(StorageLocation(kind="shelf", label="10", parent_id=rack.id))
        rows = [
            PartStorage(
                part_num="old",
                location="7",
                level="3",
                box="2",
                quantity=None,
                notes="Ungezählter Bestand",
            ),
            PartStorage(part_num="new", location="7", level="3", box="10", quantity=8),
            PartStorage(
                part_num="old",
                location="7",
                level="3",
                box='<img src=x onerror="alert(1)">',
                quantity=0,
            ),
            PartStorage(
                part_num="old", location=None, level=None, box=None, quantity=None
            ),
        ]
        db.session.add_all(rows)
        db.session.commit()
        storage_id = rows[0].id
    server = make_server("127.0.0.1", 0, app, threaded=True)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1365, "height": 1000})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route(
                "**/*",
                lambda route: (
                    route.continue_()
                    if route.request.url.startswith(origin)
                    else route.fulfill(status=200, body="")
                ),
            )
            held_requests = []

            def hold_data(route):
                held_requests.append(route)

            page.route("**/warehouse/data?**", hold_data)
            page.goto(origin + "/warehouse", wait_until="domcontentloaded")
            expect(page.locator("#warehouse-shelf")).to_be_disabled()
            expect(page.locator("#warehouse-shelf")).to_contain_text(
                "Fach wird geladen"
            )
            expect(page.locator("#warehouse-shelf")).not_to_contain_text("Alle Fächer")
            page.unroute("**/warehouse/data?**", hold_data)
            assert held_requests
            for route in held_requests:
                route.continue_()
            expect(page.locator("#warehouse-status")).to_contain_text(
                "4 Inhaltszuordnungen"
            )
            expect(page.locator("#warehouse-status")).to_contain_text(
                "0 physisch erfasste Einheiten"
            )
            expect(page.locator("#warehouse-shelf")).to_have_value(str(shelf_id))
            expect(page.locator(".warehouse-shelf")).to_have_count(1)
            other_shelf = page.locator("#warehouse-shelf option").evaluate_all(
                "nodes => nodes.find(n => n.text.endsWith('Fach 10')).value"
            )
            page.locator("#warehouse-shelf").select_option(other_shelf)
            page.reload()
            expect(page.locator("#warehouse-shelf")).to_have_value(other_shelf)
            expect(page.locator(".warehouse-shelf")).to_have_count(1)
            page.evaluate(
                "localStorage.setItem('brick-manager.warehouse.last-shelf', '999999999')"
            )
            page.reload()
            expect(page.locator("#warehouse-shelf")).to_have_value(str(shelf_id))
            page.locator("#warehouse-shelf").select_option("")
            expect(page.locator(".warehouse-shelf")).to_have_count(2)
            page.reload()
            expect(page.locator("#warehouse-shelf")).to_have_value(str(shelf_id))
            page.locator("#warehouse-shelf").select_option(str(shelf_id))
            cards = page.locator(".warehouse-shelf .warehouse-legacy-card")
            expect(cards).to_have_count(3)
            labels = cards.locator("strong").all_text_contents()
            assert labels.index("Box 2") < labels.index("Box 10"), labels
            expect(cards.first.locator(".warehouse-part-preview")).to_have_count(1)
            expect(cards.first.locator(".warehouse-part-preview")).to_contain_text(
                "Teil"
            )
            positions = cards.evaluate_all(
                "nodes => nodes.map(n => {const r=n.getBoundingClientRect();return {x:r.x,y:r.y};})"
            )
            assert positions[0]["y"] > positions[1]["y"] > positions[2]["y"], positions
            assert positions[0]["x"] == positions[1]["x"] == positions[2]["x"], (
                positions
            )
            page.locator("#warehouse-column-rows").select_option("2")
            positions = cards.evaluate_all(
                "nodes => nodes.map(n => {const r=n.getBoundingClientRect();return {x:r.x,y:r.y};})"
            )
            assert positions[0]["y"] > positions[1]["y"], positions
            assert positions[2]["x"] > positions[0]["x"], positions
            page.locator("#warehouse-list").click()
            positions = cards.evaluate_all(
                "nodes => nodes.map(n => n.getBoundingClientRect().y)"
            )
            assert positions == sorted(positions), positions
            page.locator("#warehouse-front").click()
            expect(page.locator("#warehouse-space")).to_contain_text(
                "Freie Stellfläche ist deshalb noch nicht bestimmbar"
            )
            expect(page.locator("#warehouse-space")).not_to_contain_text("[]")
            cards.filter(has=page.locator("strong", has_text="Box 2")).click()
            expect(page.locator("#warehouse-details")).to_contain_text("ungezählt")
            expect(page.locator("#warehouse-details")).to_contain_text(
                "Ungezählter Bestand"
            )
            expect(page.locator("#detail-title")).to_be_focused()
            page.get_by_role("button", name=f"#{storage_id} Behälter zuordnen").click()
            expect(page.locator('#warehouse-content-form [name="id"]')).to_have_value(
                str(storage_id)
            )
            expect(
                page.locator('#warehouse-content-form [name="quantity"]')
            ).to_have_value("")
            expect(
                page.locator('#warehouse-content-form [name="storage_unit_id"]')
            ).to_be_focused()
            page.locator(".warehouse-unlocated summary").click()
            page.get_by_role(
                "button", name="Box ohne Beschriftung", exact=False
            ).click()
            expect(page.locator("#warehouse-details")).to_contain_text(
                "Das Fach ist nicht eindeutig zugeordnet"
            )
            assert page.locator("#warehouse-layout img").count() == 0
            assert '<img src=x onerror="alert(1)">' in " ".join(labels)

            def api(path, payload, method="POST"):
                result = page.evaluate(
                    """async ({path, payload, method}) => {
                    const response = await fetch('/warehouse' + path, {method,
                        headers: {'Content-Type':'application/json', 'X-CSRF-Token':document.querySelector('meta[name="warehouse-csrf"]').content},
                        body:JSON.stringify(payload)});
                    return {status:response.status, body:await response.json()};
                }""",
                    {"path": path, "payload": payload, "method": method},
                )
                assert result["status"] in [200, 201], result
                return result["body"]

            ctype = api(
                "/types",
                {
                    "name": "Confirmed test box",
                    "width_mm": 100,
                    "depth_mm": 80,
                    "height_mm": 50,
                    "dimensions_status": "measured",
                    "access_mode": "front_open",
                },
            )
            unit = api("/units", {"type_id": ctype["id"], "label": "2"})
            api(
                f"/contents/{storage_id}",
                {
                    "storage_unit_id": unit["id"],
                    "quantity": None,
                    "notes": "Ungezählter Bestand",
                    "reason": "Test physical verification",
                },
                "PATCH",
            )
            page.locator("#warehouse-refresh").click()
            expect(page.locator("#warehouse-status")).to_contain_text(
                "3 bestehende Beschriftungsgruppen"
            )
            expect(
                page.locator(".warehouse-shelf .warehouse-legacy-card")
            ).to_have_count(2)
            assert (
                "Box 2"
                not in page.locator(
                    ".warehouse-shelf .warehouse-legacy-card strong"
                ).all_text_contents()
            )
            for width in [1365, 390]:
                page.set_viewport_size({"width": width, "height": 900})
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth + 1"
                ), f"overflow at {width}"
            assert not errors, errors
            browser.close()
        print(
            "PASS: legacy labels, natural ordering, quantities, form selection, missing address, safe text, desktop/mobile bounds"
        )
    finally:
        server.shutdown()


if __name__ == "__main__":
    run()
