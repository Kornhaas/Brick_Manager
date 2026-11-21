"""Task pages must stay separate while sharing navigation and session protection."""

from html.parser import HTMLParser

import pytest
from models import CategoryStorageRule, RebrickablePartCategories, StorageLocation, db


class PageElements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = set()
        self.active_links = []
        self.tokens = []
        self.ids = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "form":
            self.forms.add(attributes.get("id"))
        if tag == "a" and attributes.get("aria-current") == "page":
            self.active_links.append(attributes.get("href"))
        if tag == "meta" and attributes.get("name") == "warehouse-csrf":
            self.tokens.append(attributes.get("content"))


PAGES = {
    "": {"warehouse-search-form"},
    "/intake": {"warehouse-search-form", "warehouse-move-form"},
    "/reorganize": {"warehouse-move-form"},
    "/box-types": {"warehouse-type-form", "warehouse-rule-form"},
    "/locations": {"warehouse-location-form"},
    "/capture": {
        "warehouse-unit-form",
        "warehouse-placement-form",
        "warehouse-unit-update-form",
        "warehouse-partition-form",
        "warehouse-content-form",
    },
    "/settings-page": {
        "warehouse-category-form",
        "warehouse-preference-form",
        "warehouse-planned-set-form",
        "warehouse-settings-form",
    },
}


@pytest.mark.parametrize("path, expected_forms", PAGES.items())
def test_task_page_contains_only_its_forms(client, path, expected_forms):
    response = client.get("/warehouse" + path)
    assert response.status_code == 200
    page = PageElements(response.get_data(as_text=True))
    assert page.forms == expected_forms
    assert len(page.ids) == len(set(page.ids)), "duplicate IDs break form bindings"
    assert page.tokens and page.tokens[0]
    assert "/warehouse" + path in page.active_links
    assert "warehouse-status" in page.ids
    assert "warehouse-error" in page.ids


def test_navigation_reuses_session_token(client):
    tokens = {
        PageElements(client.get("/warehouse" + path).get_data(as_text=True)).tokens[0]
        for path in PAGES
    }
    assert len(tokens) == 1


@pytest.mark.parametrize("path", PAGES)
def test_disabled_warehouse_hides_every_task_page(app, client, monkeypatch, path):
    monkeypatch.setitem(app.config, "WAREHOUSE_ENABLED", False)
    response = client.get("/warehouse" + path)
    assert response.status_code == 404
    assert response.get_json() == {"error": "Lageransicht ist deaktiviert."}


def test_unknown_task_page_is_not_rendered_as_overview(client):
    assert client.get("/warehouse/not-a-task").status_code == 404


def test_category_settings_offer_catalog_names_and_keep_numeric_save_contract(client):
    db.session.add_all(
        [
            RebrickablePartCategories(id=17, name="Plates"),
            RebrickablePartCategories(id=4, name="Bricks & Slopes"),
        ]
    )
    location = StorageLocation(kind="zone", label="Active")
    db.session.add(location)
    db.session.commit()
    settings = client.get("/warehouse/settings").get_json()
    assert settings["categories"] == [
        {"id": 4, "name": "Bricks & Slopes"},
        {"id": 17, "name": "Plates"},
    ]
    html = client.get("/warehouse/settings-page").get_data(as_text=True)
    assert 'name="category_id" data-options="categories"' in html
    assert "Kategorie-ID" not in html
    saved = client.post(
        "/warehouse/category-rules",
        json={"category_id": 4, "location_id": location.id},
    )
    assert saved.status_code == 201
    rule = client.get("/warehouse/settings").get_json()["category_rules"][0]
    assert rule["category_name"] == "Bricks & Slopes"
    assert rule["category_id"] == 4
    assert db.session.get(CategoryStorageRule, rule["id"]).category_id == 4


def test_category_settings_report_empty_catalog_and_reject_unknown_category(client):
    assert client.get("/warehouse/settings").get_json()["categories"] == []
    location = StorageLocation(kind="zone", label="Active")
    db.session.add(location)
    db.session.commit()
    response = client.post(
        "/warehouse/category-rules",
        json={"category_id": 999, "location_id": location.id},
    )
    assert response.status_code == 404
    assert CategoryStorageRule.query.count() == 0
