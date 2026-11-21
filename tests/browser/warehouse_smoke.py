"""Optional real-browser warehouse acceptance using an isolated test application.

Requires Playwright with Chromium installed, for example:
PYTHONPATH=/tmp/brick-browser PLAYWRIGHT_BROWSERS_PATH=/tmp/brick-browser-cache \
  poetry run python tests/browser/warehouse_smoke.py
No production app import, remote requests or real collection database is used.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "brick_manager"))

from models import CatalogGeneration, RebrickableSets, db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_part_history import catalog_fixture  # noqa: E402


def run():
    app = create_test_app()
    # The shared fixture factory binds a disposable SQLite memory database.
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=True)
    with app.app_context():
        db.create_all()
        catalog_fixture()
        db.session.get(CatalogGeneration, 1).completed_at = datetime.now()
        db.session.get(RebrickableSets, "new-set").year = datetime.now().year
        db.session.commit()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    checks = []
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, channel=os.environ.get("BRICK_BROWSER_CHANNEL")
            )
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
            page.goto(origin + "/warehouse")
            expect(page.locator("#warehouse-status")).to_contain_text("Einheiten")

            def submit(form_id, path, fields, method="POST", status=201):
                task = {
                    "warehouse-location-form": "locations",
                    "warehouse-type-form": "box-types",
                    "warehouse-rule-form": "box-types",
                    "warehouse-move-form": "reorganize",
                    "warehouse-category-form": "settings-page",
                }.get(form_id, "capture")
                if not page.url.startswith(origin + "/warehouse/" + task):
                    page.goto(origin + "/warehouse/" + task)
                    expect(page.locator("#warehouse-status")).not_to_have_text(
                        "Lager wird geladen …"
                    )
                form = page.locator("#" + form_id)
                form.evaluate(
                    "node => {for(let p=node.parentElement;p;p=p.parentElement) if(p.tagName==='DETAILS') p.open=true;}"
                )
                for name, value in fields.items():
                    field = form.locator(f'[name="{name}"]')
                    tag = field.evaluate("node => node.tagName")
                    kind = field.get_attribute("type")
                    if kind == "checkbox":
                        field.set_checked(bool(value))
                    elif tag == "SELECT":
                        field.select_option(str(value) if value is not None else "")
                    else:
                        field.fill(str(value) if value is not None else "")
                button = form.locator('button:not([type="button"])').last
                with page.expect_response(
                    lambda response: (
                        response.url == origin + "/warehouse" + path
                        and response.request.method == method
                    )
                ) as received:
                    button.click()
                response = received.value
                assert response.status == status, (
                    path,
                    response.status,
                    response.text(),
                )
                expect(button).to_be_enabled()
                expect(page.locator("#warehouse-error")).to_be_hidden()
                return response.json()

            zone = submit(
                "warehouse-location-form",
                "/locations",
                {"kind": "zone", "label": "Browser test zone"},
            )
            rack = submit(
                "warehouse-location-form",
                "/locations",
                {
                    "kind": "rack",
                    "label": "Representative rack",
                    "parent_id": zone["id"],
                },
            )
            shelf = submit(
                "warehouse-location-form",
                "/locations",
                {
                    "kind": "shelf",
                    "label": "Mixed browser compartment",
                    "parent_id": rack["id"],
                },
            )
            submit(
                "warehouse-location-form",
                "/locations",
                {
                    "kind": "shelf",
                    "label": "Second browser compartment",
                    "parent_id": rack["id"],
                },
            )
            checks.append("Zone/rack/shelf forms with no fixed pilot identity")
            page.goto(origin + "/warehouse/box-types")
            page.locator("#warehouse-seed").evaluate(
                "node => node.closest('details').open = true"
            )
            page.locator("#warehouse-seed").click()
            expect(
                page.locator('#warehouse-type-form [name="id"] option')
            ).to_have_count(10)
            ctype = submit(
                "warehouse-type-form",
                "/types",
                {
                    "name": "Browser measured box",
                    "width_mm": 100,
                    "depth_mm": 80,
                    "height_mm": 50,
                    "dimensions_status": "measured",
                    "access_mode": "front_open",
                },
            )
            units = []
            for label in ["3", "4", "6"]:
                units.append(
                    submit(
                        "warehouse-unit-form",
                        "/units",
                        {"type_id": ctype["id"], "label": label},
                    )
                )
            for index, unit in enumerate(units):
                submit(
                    "warehouse-placement-form",
                    f"/units/{unit['id']}/placement",
                    {
                        "unit_id": unit["id"],
                        "shelf_id": shelf["id"],
                        "support_unit_id": None,
                        "relation_kind": "on_shelf",
                        "order_left": index,
                        "x_mm": index * 110,
                        "depth_offset_mm": 0,
                    },
                )
            checks.append(
                "Type setup, measured type, units and observed placement via actual forms"
            )

            source = submit(
                "warehouse-content-form",
                "/contents",
                {
                    "id": None,
                    "part_num": "old",
                    "color_id": 1,
                    "storage_unit_id": units[0]["id"],
                    "quantity": 10,
                },
            )
            submit(
                "warehouse-content-form",
                "/contents",
                {
                    "id": None,
                    "part_num": "old",
                    "color_id": 1,
                    "storage_unit_id": units[1]["id"],
                    "quantity": 2,
                },
            )
            for unit in units[:2]:
                submit(
                    "warehouse-unit-update-form",
                    f"/units/{unit['id']}",
                    {
                        "id": unit["id"],
                        "fill_state": "space",
                        "contents_complete": True,
                    },
                    method="PATCH",
                    status=200,
                )
            checks.append(
                "Initial contents and audited physical count; unknown values do not become zero"
            )
            # Exercise explicit stacking/loose support and drawer partition controls.
            setup_rows = page.request.get(origin + "/warehouse/data").json()
            types = {row["name"]: row["id"] for row in setup_rows["types"]}
            submit(
                "warehouse-rule-form",
                "/stack-rules",
                {
                    "lower_type_id": ctype["id"],
                    "upper_type_id": ctype["id"],
                    "relation_kind": "stacked",
                    "verified": True,
                    "height_increment_mm": 45,
                    "max_count": 4,
                },
            )
            top = submit(
                "warehouse-unit-form", "/units", {"type_id": ctype["id"], "label": "9"}
            )
            submit(
                "warehouse-placement-form",
                f"/units/{top['id']}/placement",
                {
                    "unit_id": top["id"],
                    "shelf_id": None,
                    "support_unit_id": units[2]["id"],
                    "x_mm": 0,
                    "depth_offset_mm": 0,
                    "relation_kind": "stacked",
                    "observed_unverified": False,
                },
            )
            cyeer = submit(
                "warehouse-unit-form",
                "/units",
                {"type_id": types["CYEER 750 ml"], "label": "Loose base"},
            )
            cup = submit(
                "warehouse-unit-form",
                "/units",
                {"type_id": types["Feinkost 125 ml"], "label": "Loose cup"},
            )
            submit(
                "warehouse-placement-form",
                f"/units/{cyeer['id']}/placement",
                {
                    "unit_id": cyeer["id"],
                    "shelf_id": shelf["id"],
                    "support_unit_id": None,
                    "relation_kind": "on_shelf",
                    "order_left": 7,
                },
            )
            submit(
                "warehouse-rule-form",
                "/stack-rules",
                {
                    "lower_type_id": types["CYEER 750 ml"],
                    "upper_type_id": types["Feinkost 125 ml"],
                    "relation_kind": "loose_on",
                    "verified": True,
                    "height_increment_mm": None,
                    "max_count": None,
                },
            )
            submit(
                "warehouse-placement-form",
                f"/units/{cup['id']}/placement",
                {
                    "unit_id": cup["id"],
                    "shelf_id": None,
                    "support_unit_id": cyeer["id"],
                    "relation_kind": "loose_on",
                },
            )
            page.goto(origin + "/warehouse")
            expect(
                page.locator(f'.warehouse-unit[data-unit-id="{cup["id"]}"]').first
            ).to_contain_text("Lose Auflage")
            cabinet = submit(
                "warehouse-unit-form",
                "/units",
                {"type_id": types["STANLEY 1-93-978"], "label": "Drawer cabinet"},
            )
            assert len(cabinet["children"]) == 9
            drawer = cabinet["children"][0]
            partition = submit(
                "warehouse-partition-form",
                f"/units/{drawer['id']}/partitions",
                {"id": drawer["id"], "partition_count": 3},
                status=200,
            )
            assert len(partition["children"]) == 3
            checks.append(
                "Verified stacking, distinct loose CYEER support, magazine and three drawer compartments"
            )

            move = submit(
                "warehouse-move-form",
                "/moves",
                {
                    "kind": "quantity",
                    "source_storage_id": source["id"],
                    "target_unit_id": units[1]["id"],
                    "quantity": 4,
                    "reason": "Browser partial transfer",
                    "capacity_confirmed": True,
                },
            )
            article = page.locator(".warehouse-move").filter(
                has_text="Browser partial transfer"
            )
            expect(article).to_contain_text("Umbuchungsmenge 4")
            with page.expect_response(
                lambda response: response.url.endswith(f"/moves/{move['id']}/plan")
            ) as planned:
                article.get_by_role(
                    "button", name="Plan übernehmen und reservieren"
                ).click()
            assert planned.value.status == 200
            expect(
                article.get_by_role("button", name="Physisch umgeräumt – bestätigen")
            ).to_be_enabled()
            page.on("dialog", lambda dialog: dialog.accept())
            with page.expect_response(
                lambda response: response.url.endswith(f"/moves/{move['id']}/confirm")
            ) as confirmed:
                article.get_by_role(
                    "button", name="Physisch umgeräumt – bestätigen"
                ).click()
            assert confirmed.value.status == 200
            expect(article).to_contain_text("Physisch bestätigt")
            checks.append(
                "Draft / reservation / explicit physical confirmation through actual controls"
            )

            submit(
                "warehouse-category-form",
                "/category-rules",
                {"category_id": 1, "location_id": rack["id"]},
            )
            page.goto(origin + "/warehouse")
            search_form = page.locator("#warehouse-search-form")
            search_form.locator('[name="part_num"]').fill("old")
            search_form.locator('[name="color_id"]').fill("1")
            search_form.get_by_role("button").click()
            expect(page.locator("#warehouse-search-results")).to_contain_text(
                "Representative rack"
            )
            expect(page.locator("#warehouse-search-results")).to_contain_text("Menge 6")
            page.goto(origin + "/warehouse/reorganize")
            page.locator("#warehouse-shelf").select_option(str(shelf["id"]))
            page.locator("#warehouse-archive").click()
            expect(page.locator("#warehouse-archive-results")).to_contain_text(
                "Eigenbedarf unbekannt · bitte prüfen"
            )
            expect(page.locator("#warehouse-archive-results")).to_contain_text(
                "Leerer Behälter gibt keine Stellfläche frei"
            )
            checks.append(
                "Part locations, unknown-demand category default and manual archive review hint"
            )

            page.set_viewport_size({"width": 390, "height": 844})
            page.locator("#warehouse-list").click()
            expect(page.locator("#warehouse-list")).to_have_attribute(
                "aria-pressed", "true"
            )
            unit_button = page.locator(
                f'.warehouse-unit[data-unit-id="{units[0]["id"]}"]'
            ).first
            unit_button.focus()
            page.keyboard.press("Enter")
            expect(page.locator("#warehouse-details")).to_contain_text("Gezählte Menge")
            expect(page.locator("#detail-title")).to_be_focused()
            checks.append(
                "390px viewport, list alternative, keyboard unit selection and detail focus"
            )
            page.goto(origin + "/warehouse?part_num=old&color_id=1")
            expect(
                page.locator('#warehouse-search-form [name="part_num"]')
            ).to_have_value("old")
            expect(page.locator("#warehouse-search-results")).to_contain_text("Menge 6")
            checks.append(
                "Part-search deep link preloads matching locations and intake suggestion"
            )
            assert not errors, errors
            expect(page.locator("#warehouse-error")).to_be_hidden()
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()
    print(
        json.dumps(
            {"status": "passed", "checks": checks, "javascript_errors": errors},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
