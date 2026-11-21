"""Exercise task pages in Chromium against a disposable in-memory database.

Requires Playwright and an installed Chromium browser. Set BRICK_BROWSER_CHANNEL
to msedge or chrome to use an installed browser. Never imports production app.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "brick_manager"))

from models import db  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_part_history import catalog_fixture  # noqa: E402


def run():
    app = create_test_app()
    app.config.update(WTF_CSRF_ENABLED=True)
    with app.app_context():
        db.create_all()
        catalog_fixture()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    errors = []
    checks = []
    with TemporaryDirectory(prefix="warehouse-pages-artifacts-") as artifacts:
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
                        or route.request.url.startswith(
                            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/"
                        )
                        else route.fulfill(status=200, body="")
                    ),
                )

                def visit(path):
                    page.goto(origin + "/warehouse" + path)
                    expect(page.locator("#warehouse-status")).not_to_have_text(
                        "Lager wird geladen …"
                    )
                    expect(page.locator("#warehouse-error")).to_be_hidden()
                    expect(
                        page.locator(
                            'nav[aria-label="Lagerverwaltung"] a[aria-current="page"]'
                        )
                    ).to_have_attribute(
                        "href",
                        re.compile(
                            r"(?:https?://[^/]+)?/warehouse"
                            + re.escape(path)
                            + r"(?:\?.*)?$"
                        ),
                    )

                def submit(form_id, path, fields, method="POST"):
                    form = page.locator("#" + form_id)
                    for name, value in fields.items():
                        field = form.locator(f'[name="{name}"]')
                        if field.evaluate("node => node.tagName") == "SELECT":
                            field.select_option(str(value))
                        else:
                            field.fill(str(value))
                    with page.expect_response(
                        lambda response: (
                            response.url == origin + "/warehouse" + path
                            and response.request.method == method
                        )
                    ) as received:
                        form.locator('button:not([type="button"])').last.click()
                    assert received.value.ok, received.value.text()
                    expect(
                        form.locator('button:not([type="button"])').last
                    ).to_be_enabled()
                    expect(page.locator("#warehouse-error")).to_be_hidden()
                    return received.value.json()

                for path in [
                    "",
                    "/intake",
                    "/reorganize",
                    "/box-types",
                    "/locations",
                    "/capture",
                    "/settings-page",
                ]:
                    visit(path)
                checks.append("seven task pages load without script errors")

                visit("/box-types")
                box_type = submit(
                    "warehouse-type-form",
                    "/types",
                    {
                        "name": "Browser small box",
                        "width_mm": 120,
                        "depth_mm": 180,
                        "height_mm": 80,
                    },
                )
                selector = page.locator('#warehouse-type-form [name="id"]')
                selector.select_option(str(box_type["id"]))
                expect(
                    page.locator('#warehouse-type-form [name="name"]')
                ).to_have_value("Browser small box")
                submit(
                    "warehouse-type-form",
                    f"/types/{box_type['id']}",
                    {"width_mm": 125},
                    "PATCH",
                )
                checks.append("create and edit box dimensions")
                selector.select_option("")
                expect(
                    page.locator('#warehouse-type-form [name="name"]')
                ).to_have_value("")
                expect(
                    page.locator('#warehouse-type-form [name="kind"]')
                ).to_be_enabled()

                visit("/locations")
                zone = submit(
                    "warehouse-location-form",
                    "/locations",
                    {"kind": "zone", "label": "Browser zone"},
                )
                rack = submit(
                    "warehouse-location-form",
                    "/locations",
                    {"kind": "rack", "label": "1", "parent_id": zone["id"]},
                )
                shelf = submit(
                    "warehouse-location-form",
                    "/locations",
                    {
                        "kind": "shelf",
                        "label": "2",
                        "parent_id": rack["id"],
                        "width_mm": 600,
                        "depth_mm": 300,
                    },
                )
                page.locator('#warehouse-location-form [name="id"]').select_option(
                    str(shelf["id"])
                )
                expect(
                    page.locator('#warehouse-location-form [name="width_mm"]')
                ).to_have_value("600")
                checks.append("create hierarchy and select shelf measurements")
                page.locator('#warehouse-location-form [name="id"]').select_option("")
                expect(
                    page.locator('#warehouse-location-form [name="label"]')
                ).to_have_value("")
                expect(
                    page.locator('#warehouse-location-form [name="kind"]')
                ).to_be_enabled()
                second_shelf = submit(
                    "warehouse-location-form",
                    "/locations",
                    {"kind": "shelf", "label": "3", "parent_id": rack["id"]},
                )
                page.locator(
                    f'#warehouse-location-list input[value="{shelf["id"]}"]'
                ).check()
                expect(page.locator("#warehouse-location-labels")).to_contain_text(
                    "Fach 2"
                )
                page.emulate_media(media="print")
                expect(page.locator("#warehouse-location-labels")).to_be_visible()
                expect(page.locator(".warehouse-location-label")).to_have_count(1)
                expect(page.locator("#warehouse-location-form")).to_be_hidden()
                expect(page.locator(".warehouse-nav")).to_be_hidden()
                page.emulate_media(media="screen")
                checks.append(
                    "new-item forms reset and selected shelf label has isolated print layout"
                )

                visit("/settings-page")
                category = page.get_by_role(
                    "combobox", name=re.compile(r"^Kategorie\b")
                )
                expect(category).to_be_enabled()
                expect(category.locator("option")).to_have_text(
                    ["Kategorie wählen", "Bricks"]
                )
                category.select_option(label="Bricks")
                saved_rule = submit(
                    "warehouse-category-form",
                    "/category-rules",
                    {"location_id": shelf["id"]},
                )
                assert saved_rule["category_id"] == 1
                expect(page.locator("#warehouse-settings-summary")).to_contain_text(
                    "Bricks →"
                )
                expect(page.locator("#warehouse-settings-summary")).not_to_contain_text(
                    "Kategorie #"
                )
                checks.append("choose category by name and save numeric rule identity")

                current_settings = page.request.get(
                    origin + "/warehouse/settings"
                ).json()
                for categories, expected_hint in [
                    (None, "Die Kategorieauswahl konnte nicht geladen werden"),
                    ([], "Im Teilekatalog sind keine Kategorien hinterlegt"),
                ]:
                    payload = dict(current_settings)
                    if categories is None:
                        payload.pop("categories")
                    else:
                        payload["categories"] = categories
                    page.route(
                        "**/warehouse/settings",
                        lambda route, _request, response_payload=payload: route.fulfill(
                            json=response_payload
                        ),
                    )
                    page.reload()
                    expect(page.locator("#warehouse-category-hint")).to_contain_text(
                        expected_hint
                    )
                    expect(
                        page.locator("#warehouse-category-hint")
                    ).not_to_contain_text("importieren")
                    expect(category).to_be_disabled()
                    expect(
                        page.locator("#warehouse-category-form button")
                    ).to_be_disabled()
                    if categories is None:
                        expect(page.locator("#warehouse-error")).to_contain_text(
                            "Die Kategorieauswahl konnte nicht geladen werden"
                        )
                    page.unroute("**/warehouse/settings")
                    visit("/settings-page")
                    expect(category).to_be_enabled()
                checks.append(
                    "missing category response differs from empty catalog and recovers on reload"
                )

                visit("/capture")
                unit = submit(
                    "warehouse-unit-form",
                    "/units",
                    {"type_id": box_type["id"], "label": "Box 12"},
                )
                submit(
                    "warehouse-placement-form",
                    f"/units/{unit['id']}/placement",
                    {"unit_id": unit["id"], "shelf_id": shelf["id"]},
                )

                visit("/intake")
                form = page.locator("#warehouse-move-form")
                expect(form.locator('[name="part_num"]')).to_be_visible()
                expect(form.locator('[name="source_storage_id"]')).to_be_hidden()
                expect(form.locator('[name="shelf_id"]')).to_be_hidden()
                expect(form.locator('[name="source_storage_id"]')).to_be_disabled()
                checks.append("intake shows only intake fields")
                form.locator('[name="capacity_confirmed"]').check()
                movement = submit(
                    "warehouse-move-form",
                    "/moves",
                    {
                        "part_num": "old",
                        "color_id": 1,
                        "quantity": 7,
                        "target_unit_id": unit["id"],
                        "reason": "Browser intake",
                    },
                )
                article = page.locator(".warehouse-move").filter(
                    has_text="Browser intake"
                )
                with page.expect_response(
                    lambda response: response.url.endswith(
                        f"/moves/{movement['id']}/plan"
                    )
                ):
                    article.get_by_role(
                        "button", name="Plan übernehmen und reservieren"
                    ).click()
                page.on("dialog", lambda dialog: dialog.accept())
                with page.expect_response(
                    lambda response: response.url.endswith(
                        f"/moves/{movement['id']}/confirm"
                    )
                ) as confirmed:
                    article.get_by_role(
                        "button", name="Physisch umgeräumt – bestätigen"
                    ).click()
                assert confirmed.value.status == 200
                expect(article).to_contain_text("Physisch bestätigt")
                checks.append(
                    "create intake draft, reserve and physically confirm seven Bricks"
                )

                visit("/reorganize")
                form = page.locator("#warehouse-move-form")
                expect(form.locator('[name="source_storage_id"]')).to_be_visible()
                expect(form.locator('[name="part_num"]')).to_be_hidden()
                form.locator('[name="kind"]').select_option("unit")
                expect(form.locator('[name="unit_id"]')).to_be_visible()
                expect(form.locator('[name="source_storage_id"]')).to_be_hidden()
                checks.append("move mode switches relevant fields")

                visit("")
                page.locator("#warehouse-shelf").select_option(str(second_shelf["id"]))
                page.goto(origin + f"/warehouse?unit_id={unit['id']}")
                expect(page.locator("#warehouse-shelf")).to_have_value(str(shelf["id"]))
                expect(page.locator("#warehouse-details")).to_contain_text("Box 12")
                checks.append(
                    "unit deep link selects correct shelf despite previously selected other shelf"
                )
                expect(
                    page.locator(f'.warehouse-unit[data-unit-id="{unit["id"]}"]').first
                ).to_contain_text("Old Bricks")
                page.locator(
                    f'.warehouse-unit[data-unit-id="{unit["id"]}"]'
                ).first.click()
                expect(page.locator("#warehouse-details")).to_contain_text("7")
                screenshot_root = Path(
                    os.environ.get(
                        "BRICK_BROWSER_SCREENSHOT",
                        str(Path(artifacts) / "warehouse-mobile.png"),
                    )
                )
                page.screenshot(
                    path=str(screenshot_root.with_name("warehouse-pages-desktop.png")),
                    full_page=True,
                )
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                )
                page.keyboard.press("Tab")
                checks.append(
                    "mobile overview fits viewport and accepts keyboard focus"
                )
                screenshot = Path(
                    os.environ.get(
                        "BRICK_BROWSER_SCREENSHOT",
                        str(Path(artifacts) / "warehouse-mobile.png"),
                    )
                )
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot), full_page=True)
                assert not errors, errors
                browser.close()
                print(
                    json.dumps(
                        {
                            "checks": checks,
                            "page_errors": errors,
                            "screenshot": str(screenshot),
                        },
                        ensure_ascii=False,
                    )
                )
        finally:
            server.shutdown()
            server.server_close()
            with app.app_context():
                db.session.remove()
                db.drop_all()
                db.engine.dispose()


if __name__ == "__main__":
    run()
