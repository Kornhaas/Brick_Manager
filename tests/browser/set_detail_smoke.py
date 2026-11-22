"""Exercise set editing in Chromium against the isolated Flask test application.

Requires Playwright and Chromium. BRICK_BROWSER_CHANNEL can select an installed
browser such as msedge. Browser host resolution is limited to loopback.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "brick_manager")]

from models import (  # noqa: E402
    USER_SET_STATUSES,
    RebrickableParts,
    RebrickableSets,
    User_Minifigures,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from playwright.sync_api import expect, sync_playwright  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from brick_manager.tests.conftest import create_test_app  # noqa: E402
from brick_manager.tests.test_set_detail import inventory, seed_set_copies  # noqa: E402

LIST_FILTERS = {
    "q": "Explorer & Research",
    "theme": "Space & Science",
    "status": "unknown",
    "label": "not-printed",
    "completion": "incomplete",
    "group": "theme",
    "sort": "box_id",
    "direction": "desc",
    "per_page": "25",
    "page": "2",
}
EXTRA_REGULAR_ROWS = 24
COMPLETE_MINIFIG_PART_ID = 101
BROWSER_SET_NAME = "Explorer & Research " + "LongCatalogNameWithoutSpaces" * 5


def seed_browser_collection():
    first, second = seed_set_copies()
    db.session.get(RebrickableSets, "1000-1").name = BROWSER_SET_NAME
    for _ in range(34):
        user_set = User_Set(set_num="1000-1", status="unknown")
        db.session.add(user_set)
        db.session.flush()
        db.session.add(
            User_Parts(part_num="3001", color_id=5, user_set_id=user_set.id, quantity=2)
        )
    for status in USER_SET_STATUSES - {"unknown"}:
        db.session.add(User_Set(set_num="1000-1", status=status))

    regular = db.session.get(User_Parts, first.regular)
    category = regular.rebrickable_part.part_cat_id
    figure_piece = RebrickableParts(
        part_num="figure-complete",
        name="0 Complete figure piece",
        part_cat_id=category,
    )
    db.session.add(figure_piece)
    db.session.flush()
    figure = User_Minifigures.query.filter_by(user_set_id=first.id).one()
    db.session.add(
        UserMinifigurePart(
            id=COMPLETE_MINIFIG_PART_ID,
            part_num=figure_piece.part_num,
            color_id=5,
            user_set_id=first.id,
            minifigure_id=figure.id,
            quantity=1,
            have_quantity=1,
        )
    )
    db.session.add_all(
        User_Parts(
            part_num=regular.part_num,
            color_id=5,
            user_set_id=first.id,
            quantity=1,
            have_quantity=0,
        )
        for _ in range(EXTRA_REGULAR_ROWS)
    )
    db.session.commit()
    return first, second


def detail_link(page, copy):
    return page.locator(f"#set-box-{copy.id}").get_by_role(
        "link", name=f"View {BROWSER_SET_NAME}, Box {copy.id}"
    )


def field(page, field_id, prefix="part_id"):
    return page.locator(f'input[name="{prefix}_{field_id}"]')


def assert_list_context(page, copy, owned):
    expect(detail_link(page, copy)).to_be_focused()
    expect(page.locator(f"#set-box-{copy.id}")).to_contain_text(
        f"{owned}/{9 + EXTRA_REGULAR_ROWS}"
    )
    url = urlsplit(page.url)
    assert url.path == "/set_maintain"
    assert url.fragment == f"set-box-{copy.id}"
    assert parse_qs(url.query) == {
        key: [value]
        for key, value in {**LIST_FILTERS, "returned_box": str(copy.id)}.items()
    }


def save(page):
    page.locator("#save-detail").click()
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "saved")


def verify_save_and_list_history(page, origin, first, second):
    page.add_init_script("""
        window.addEventListener('pageshow', event => {
            if (event.persisted && location.pathname === '/set_maintain') {
                sessionStorage.setItem('smoke-list-restored-from-bfcache', 'yes');
            }
        });
    """)
    source = f"{origin}/set_maintain?{urlencode(LIST_FILTERS)}"
    page.goto(source)
    expect(page.locator(".set-row")).to_have_count(11)
    expect(detail_link(page, second)).to_be_visible()
    link = detail_link(page, first)
    link.scroll_into_view_if_needed()
    link.focus()
    list_scroll = page.evaluate("scrollY")
    assert list_scroll > 0
    link.press("Enter")
    expect(page.locator("#set-title")).to_have_text(BROWSER_SET_NAME)
    expect(page.locator("#set-title")).to_be_focused()
    expect(page.locator(".box-identity")).to_contain_text(
        f"Box {first.id} · Set 1000-1"
    )
    assert urlsplit(page.url).path == first.path
    assert (
        set(
            page.locator('[name="status"] option').evaluate_all(
                "options => options.map(option => option.value)"
            )
        )
        == USER_SET_STATUSES
    )

    page.locator("#part-search").fill("Red")
    page.locator("#filter-mismatched-parts").check()
    page.locator("#spare-parts > summary").click()
    expect(field(page, COMPLETE_MINIFIG_PART_ID, "minifig_part_id")).to_be_hidden()
    expect(field(page, first.minifig, "minifig_part_id")).to_be_visible()
    active = page.locator("#regular-parts input").last
    active.scroll_into_view_if_needed()
    detail_scroll = page.evaluate("scrollY")
    assert detail_scroll > 0
    for value in ("2", "3", "4"):
        field(page, first.regular).fill(value)
        active.focus()
        page.evaluate("(position) => scrollTo(0, position)", detail_scroll)
        save(page)
        assert urlsplit(page.url).path == first.path
        assert abs(page.evaluate("scrollY") - detail_scroll) < 5
        expect(active).to_be_focused()
        expect(page.locator("#part-search")).to_have_value("Red")
        expect(page.locator("#filter-mismatched-parts")).to_be_checked()
        assert not page.locator("#spare-parts").evaluate("(element) => element.open")

    page.reload()
    expect(page.locator("#set-title")).to_be_focused()
    expect(field(page, first.regular)).to_have_value("4")
    page.locator("#set-back-link").click()
    assert_list_context(page, first, 6)
    assert abs(page.evaluate("scrollY") - list_scroll) < 5

    detail_link(page, first).click()
    field(page, first.regular).fill("3")
    save(page)
    page.go_back(wait_until="commit")
    assert_list_context(page, first, 5)
    assert abs(page.evaluate("scrollY") - list_scroll) < 5
    expect(page.locator(f"#set-box-{second.id}")).to_contain_text("5/8")
    print(
        "PASS: filtered page 2, three saves in place, reload, explicit and browser Back"
    )
    restored = page.evaluate(
        "sessionStorage.getItem('smoke-list-restored-from-bfcache')"
    )
    print("Back-forward cache restored the list:", restored == "yes")


def verify_retry_bulk_and_mobile(page, origin, first):
    writes = []

    def record_write(request):
        if request.method == "POST":
            writes.append((urlsplit(request.url).path, request.post_data_json))

    page.on("request", record_write)
    page.goto(origin + first.path)
    expect(page.locator("#set-title")).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert page.locator(".parts-scroll").first.evaluate(
        "(element) => element.scrollWidth > element.clientWidth"
    )
    expect(page.locator("#set-back-link")).to_have_attribute("href", "/set_maintain")
    amount = field(page, first.regular)
    expect(amount).to_have_accessible_name(
        "Brick 2 x 4 (3001), Red, Soll 5 – vorhanden"
    )
    amount.fill("2")
    page.locator("#part-search").press("Enter")
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "dirty")
    assert writes == []

    held = []
    page.route(origin + first.path, lambda route: held.append(route), times=1)
    with page.expect_request(lambda request: request.method == "POST"):
        amount.press("Enter")
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "saving")
    page.locator("#more-actions summary").click()
    page.locator("#mark-all-existing").click()
    expect(page.locator("#bulk-dialog")).to_be_visible()
    page.get_by_role("button", name="Abbrechen").click()
    expect(amount).to_have_value("2")
    assert writes == [(first.path, {f"part_id_{first.regular}": 2})]
    held[0].fulfill(
        status=503,
        content_type="application/json",
        json={"success": False, "error": "Vorübergehend nicht verfügbar"},
    )
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "error")
    expect(amount).to_have_value("2")
    expect(amount).to_have_attribute("data-saved", "3")
    page.locator("#set-back-link").focus()
    expect(page.locator("#set-back-link")).to_be_focused()
    retry = page.get_by_role("button", name="Erneut speichern")
    for _ in range(3):
        page.keyboard.press("Tab")
        if retry.evaluate("(element) => element === document.activeElement"):
            break
    expect(retry).to_be_focused()
    retry.press("Enter")
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "saved")
    expect(page.locator("#save-detail")).to_be_focused()
    expect(amount).to_have_attribute("data-saved", "2")
    assert writes == [(first.path, {f"part_id_{first.regular}": 2})] * 2

    amount.fill("4")
    amount.press("Enter")
    expect(page.locator("#regular-parts input").nth(1)).to_be_focused()
    focused = page.locator("#regular-parts input").nth(1)
    focused.press("Tab")
    expect(page.locator("#regular-parts input").nth(2)).to_be_focused()

    before_invalid = list(writes)
    amount.fill("6")
    page.locator("#save-detail").click()
    expect(page.locator("#detail-save-state")).to_have_attribute("data-state", "error")
    expect(amount).to_have_value("6")
    expect(amount).to_have_attribute("aria-invalid", "true")
    expect(amount).to_be_focused()
    assert writes == before_invalid

    page.evaluate("scrollTo(0, 0)")
    page.locator("#filter-mismatched-parts").check()
    page.locator("#part-search").fill("Brick 2 x 4")
    amount.fill("5")
    save(page)
    expect(amount).to_be_visible()
    expect(amount).to_be_focused()
    amount.press("Tab")
    expect(amount).to_be_hidden()

    before_bulk = list(writes)
    page.locator("#reset-all-to-zero").click()
    expect(page.locator("#bulk-title")).to_have_text("Alle Mengen auf 0 setzen?")
    expect(page.locator("#bulk-scope")).to_contain_text("1 Ersatzteilzeilen")
    expect(page.locator("#bulk-scope")).to_contain_text("2 Minifigurenteilezeilen")
    expect(page.locator("#bulk-scope")).to_contain_text("Davon ausgeblendet: 4")
    page.locator("#cancel-bulk").click()
    expect(field(page, first.spare)).to_have_value("1")
    assert writes == before_bulk
    page.locator("#reset-all-to-zero").click()
    page.locator("#apply-bulk").click()
    expect(field(page, first.spare)).to_have_value("0")
    expect(field(page, COMPLETE_MINIFIG_PART_ID, "minifig_part_id")).to_have_value("0")
    assert writes == before_bulk
    save(page)
    expect(page.locator("#detail-progress")).to_have_text("0 %")
    before_bulk = list(writes)
    page.locator("#mark-all-existing").click()
    page.locator("#apply-bulk").click()
    expect(amount).to_have_value("5")
    expect(field(page, first.spare)).to_have_value("1")
    expect(field(page, first.minifig, "minifig_part_id")).to_have_value("2")
    assert writes == before_bulk
    save(page)
    expect(page.locator("#detail-progress")).to_have_text("100 %")
    assert len(writes) == len(before_bulk) + 1
    assert writes[-1][0] == first.path
    assert writes[-1][1][f"minifig_part_id_{first.minifig}"] == 2
    assert writes[-1][1][f"part_id_{first.spare}"] == 1
    assert len(writes[-1][1]) == EXTRA_REGULAR_ROWS + 4
    print(
        "PASS: 390px, typed quantities, Enter/Tab, 503 and keyboard Retry, bulk drafts"
    )


def verify_dirty_leave(page, origin, first):
    source = f"{origin}/set_maintain?box_id={first.id}&status=unknown"
    page.goto(source)
    detail_link(page, first).click()
    amount = field(page, first.regular)
    amount.fill("1")
    page.locator("#set-back-link").click()
    expect(page.locator("#leave-dialog")).to_be_visible()
    page.get_by_role("button", name="Hier bleiben").click()
    expect(amount).to_have_value("1")
    expect(page.locator("#leave-dialog")).to_be_hidden()
    page.locator("#set-back-link").click()
    page.get_by_role("button", name="Verwerfen und zurück").click()
    expect(detail_link(page, first)).to_be_focused()
    page.go_back(wait_until="commit")
    expect(page.locator("#set-title")).to_be_focused()
    expect(amount).to_have_value("5")
    amount.fill("2")
    assert page.evaluate(
        "() => !window.dispatchEvent(new Event('beforeunload', {cancelable: true}))"
    )
    amount.fill("5")
    page.locator('[name="status"]').select_option("sealed")
    page.locator("#set-back-link").click()
    page.get_by_role("button", name="Speichern und zurück").click()
    expect(page.locator("#return-notice")).to_be_visible()
    expect(page.locator("#set-results-heading")).to_be_focused()
    expect(page.locator(".set-row")).to_have_count(0)
    query = parse_qs(urlsplit(page.url).query)
    assert query["status"] == ["unknown"]
    assert query["box_id"] == [str(first.id)]
    print("PASS: stay, discard, save and return, missing result notice and focus")


def verify_legacy_minifigure_wrapper(page, origin, first):
    # The current list links to a page. Supply the structural elements from a
    # previously loaded inline editor to exercise its still-served script.
    page.route(
        "**/smoke-legacy-set-detail",
        lambda route: route.fulfill(
            status=200,
            content_type="text/html",
            body=f"""
            <button class="view-details" data-user-set-id="{first.id}">View</button>
            <button id="confirmStatusChange">Confirm</button>
            <div id="sets-table"></div>
            <section id="set-details">
              <input id="user-set-id"><input id="status">
              <label><input id="filter-mismatched-parts" type="checkbox">Mismatches</label>
              <table><tbody id="non-spare-parts-table-body"></tbody></table>
              <table><tbody id="spare-parts-table-body"></tbody></table>
              <table><tbody id="minifigs-table-body"></tbody></table>
            </section>
            <script src="/static/js/set_maintenance.js"></script>
            """,
        ),
    )
    page.goto(origin + "/smoke-legacy-set-detail")
    page.get_by_role("button", name="View").click()
    complete = field(page, COMPLETE_MINIFIG_PART_ID, "minifig_part_id")
    expect(complete).to_be_visible()
    expect(complete).to_have_value("1")
    missing = field(page, first.minifig, "minifig_part_id")
    expect(missing).to_have_value("0")
    page.get_by_role("checkbox", name="Mismatches").check()
    expect(complete).to_be_hidden()
    expect(missing).to_be_visible()
    print("PASS: legacy mismatches leave an incomplete sibling minifigure row visible")


def run():
    app = create_test_app()
    with app.app_context():
        db.create_all()
        first, second = seed_browser_collection()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                channel=os.environ.get("BRICK_BROWSER_CHANNEL"),
                args=["--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"],
                ignore_default_args=["--disable-back-forward-cache"],
            )
            legacy = browser.new_page()
            legacy.on("pageerror", lambda error: errors.append(str(error)))
            verify_legacy_minifigure_wrapper(legacy, origin, first)
            legacy.close()
            desktop = browser.new_page(viewport={"width": 1365, "height": 900})
            desktop.on("pageerror", lambda error: errors.append(str(error)))
            verify_save_and_list_history(desktop, origin, first, second)
            mobile = browser.new_page(viewport={"width": 390, "height": 844})
            mobile.on("pageerror", lambda error: errors.append(str(error)))
            verify_retry_bulk_and_mobile(mobile, origin, first)
            verify_dirty_leave(desktop, origin, first)
            assert not errors, errors
            browser.close()
        with app.app_context():
            assert inventory(first) == ("sealed", 5, 1, 2)
            assert inventory(second) == ("unknown", 4, 1, 0)
    finally:
        server.shutdown()
        server_thread.join()
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()


if __name__ == "__main__":
    run()
