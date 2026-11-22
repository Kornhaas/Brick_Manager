"""Every reachable workspace must share the same accessible application frame."""

from html.parser import HTMLParser

import pytest
from flask import render_template

from brick_manager.tests.test_set_detail import seed_set_copies


class AppFrame(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.main_count = 0
        self.headings = 0
        self.page_headers = 0
        self.ids = []
        self.styles = []
        self.skips = []
        self.bootstrap_scripts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self.main_count += 1
        if tag == "h1":
            self.headings += 1
        if "bm-page-header" in attrs.get("class", "").split():
            self.page_headers += 1
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.styles.append(attrs["href"])
        if tag == "a" and "bm-skip" in attrs.get("class", "").split():
            self.skips.append(attrs["href"])
        if tag == "script" and "bootstrap.bundle" in attrs.get("src", ""):
            self.bootstrap_scripts.append(attrs["src"])


PAGES = [
    "/",
    "/dashboard",
    "/details/missing_parts",
    "/ai_detection",
    "/manual_entry",
    "/lookup_part",
    "/part_location",
    "/box_maintenance",
    "/set_search",
    "/set_maintain",
    "/set_maintain/1/details",
    "/building_instructions",
    "/missing_parts",
    "/import_data",
    "/token_management",
    "/admin/sync",
    "/add_to_storage/3001",
    "/warehouse",
    "/warehouse/intake",
    "/warehouse/reorganize",
    "/warehouse/box-types",
    "/warehouse/locations",
    "/warehouse/capture",
    "/warehouse/settings-page",
]


def assert_frame(html):
    frame = AppFrame(html)
    assert html.lower().count("<!doctype html>") == 1
    assert frame.main_count == 1, "one main landmark for keyboard/screen-reader use"
    assert frame.headings == 1, "each workspace has one primary heading"
    assert frame.page_headers == 1, "shared page-header component is required"
    assert frame.ids.count("main-content") == 1
    assert len(frame.ids) == len(set(frame.ids)), (
        "duplicate IDs break existing controllers"
    )
    assert frame.skips == ["#main-content"]
    shared = [url for url in frame.styles if "/css/design-system.css" in url]
    bootstrap = [url for url in frame.styles if "bootstrap@" in url]
    assert len(shared) == len(bootstrap) == 1
    assert frame.styles.index(shared[0]) > frame.styles.index(bootstrap[0])
    assert len(frame.bootstrap_scripts) == 1


@pytest.mark.parametrize("path", PAGES)
def test_all_workspaces_use_one_frame(client, app, tmp_path, monkeypatch, path):
    seed_set_copies()
    monkeypatch.setitem(app.config, "INSTRUCTIONS_FOLDER", str(tmp_path))
    response = client.get(path)
    assert response.status_code == 200, path
    assert_frame(response.get_data(as_text=True))


@pytest.mark.parametrize(
    "template, context, message",
    [
        ("results.html", {"result": {"items": []}}, "No results found."),
        (
            "error.html",
            {"message": "A recoverable test error"},
            "A recoverable test error",
        ),
    ],
)
def test_result_and_error_pages_share_the_frame(app, template, context, message):
    with app.test_request_context("/"):
        html = render_template(template, **context)
    assert_frame(html)
    assert message in html


def test_multiple_scan_matches_keep_independent_controls(app):
    """Each detected part needs its own valid storage editor and inventory table."""
    items = [
        {
            "id": number,
            "name": "Brick " + number,
            "score": 0.97,
            "img_url": "/static/brick-icon.svg",
            "lookup_info": None,
            "missing_sets": [{"part_id": index, "needed": 5, "have": 1}],
        }
        for index, number in enumerate(("3001", "3020"), start=1)
    ]
    with app.test_request_context("/"):
        html = render_template("results.html", result={"items": items})
    assert_frame(html)
    for number in ("3001", "3020"):
        assert f'id="missing-sets-table-{number}"' in html
        assert f'for="input-location-{number}"' in html
        assert (
            f'id="storage-edit-{number}" class="alert alert-info" '
            'role="alert" style="">'
        ) in html
