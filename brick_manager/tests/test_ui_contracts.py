"""Server-rendered and JavaScript UI contracts for collection workflows."""

from pathlib import Path
from unittest.mock import patch

import pytest
from models import (
    RebrickableColors,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    db,
)


@pytest.fixture
def collection_records():
    """Create the smallest catalog and collection needed by dashboard views."""
    category = RebrickablePartCategories(name="Brick")
    color = RebrickableColors(id=1, name="Red", rgb="C91A09", is_trans=False)
    theme = RebrickableThemes(name="Space & Science")
    db.session.add_all([category, color, theme])
    db.session.flush()

    part = RebrickableParts(
        part_num="3001", name="Brick 2 x 4", part_cat_id=category.id
    )
    active_template = RebrickableSets(
        set_num="1000-1",
        name="Explorer & Research",
        year=2024,
        theme_id=theme.id,
        num_parts=10,
    )
    loose_template = RebrickableSets(
        set_num="1001-1",
        name="Loose Bricks",
        year=2024,
        theme_id=theme.id,
        num_parts=3,
    )
    db.session.add_all([part, active_template, loose_template])
    db.session.flush()

    active_set = User_Set(set_num=active_template.set_num, status="unknown")
    loose_set = User_Set(set_num=loose_template.set_num, status="konvolut")
    db.session.add_all([active_set, loose_set])
    db.session.flush()

    db.session.add_all(
        [
            User_Parts(
                part_num=part.part_num,
                color_id=color.id,
                quantity=10,
                have_quantity=4,
                user_set_id=active_set.id,
                is_spare=True,
            ),
            User_Parts(
                part_num=part.part_num,
                color_id=color.id,
                quantity=3,
                have_quantity=1,
                user_set_id=loose_set.id,
            ),
        ]
    )
    db.session.commit()
    return active_set


def test_landing_page_exposes_core_collection_workflows(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Welcome to Brick Manager" in response.data
    assert b"Start Scanning" in response.data
    assert b'href="/set_maintain"' in response.data
    assert b'href="/missing_parts"' in response.data


def test_dashboard_renders_owned_missing_and_spare_part_totals(
    client, collection_records
):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"<h2>4</h2>\n                    <p>Total Parts Owned</p>" in response.data
    assert b"<h2>6</h2>\n                        <p>Missing Parts</p>" in response.data
    assert (
        b"<h2>6</h2>\n                        <p>Missing Spare Parts</p>"
        in response.data
    )
    assert (
        b"<h2>1</h2>\n                    <p>Total Konvolut Parts Owned</p>"
        in response.data
    )
    assert (
        b"<h2>2</h2>\n                        <p>Missing Konvolut Parts</p>"
        in response.data
    )


def test_set_maintenance_renders_escaped_collection_data_and_ui_hooks(
    client, collection_records
):
    response = client.get("/set_maintain")

    assert response.status_code == 200
    assert b"1000-1" in response.data
    assert b"Explorer &amp; Research" in response.data
    assert b"Space &amp; Science" in response.data
    assert b"4/10" in response.data
    assert b"40.0%" in response.data
    assert b'id="search-input"' in response.data
    assert b'id="sets-table-main"' in response.data
    assert b"/static/js/set_maintenance.js" in response.data


def test_dashboard_quantity_update_clamps_and_persists(client, collection_records):
    part = User_Parts.query.filter_by(user_set_id=collection_records.id).first()

    response = client.post(
        "/update_quantity",
        json={"changes": [{"part_id": part.id, "new_quantity": 99}]},
    )

    assert response.status_code == 200
    assert response.json == {"message": "1 records updated successfully!"}
    assert db.session.get(User_Parts, part.id).have_quantity == 10


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"changes": []}, {"changes": ["invalid"]}],
)
def test_dashboard_quantity_update_rejects_malformed_changes(client, payload):
    response = client.post("/update_quantity", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "change",
    [
        {"part_id": True, "new_quantity": 1},
        {"part_id": 1, "new_quantity": True},
        {"part_id": 1, "new_quantity": "1"},
    ],
)
def test_dashboard_quantity_update_rejects_invalid_scalar_types(client, change):
    response = client.post("/update_quantity", json={"changes": [change]})

    assert response.status_code == 400


def test_dashboard_quantity_update_validates_the_full_batch_before_mutating(
    client, collection_records
):
    part = User_Parts.query.filter_by(user_set_id=collection_records.id).first()

    response = client.post(
        "/update_quantity",
        json={
            "changes": [
                {"part_id": part.id, "new_quantity": 10},
                {"part_id": 2, "new_quantity": "invalid"},
            ]
        },
    )

    assert response.status_code == 400
    assert db.session.get(User_Parts, part.id).have_quantity == 4


def test_dashboard_missing_parts_detail_renders_enriched_collection_data(
    client, collection_records
):
    with patch(
        "routes.dashboard.load_part_lookup",
        return_value={"3001": {"location": "A", "level": "1", "box": "7"}},
    ):
        response = client.get("/details/missing_parts")

    assert response.status_code == 200
    assert b"Missing Parts" in response.data
    assert b"Brick 2 x 4" in response.data
    assert b"Location: A, Level: 1, Box: 7" in response.data


def test_dashboard_rejects_unknown_detail_category(client):
    with patch("routes.dashboard.load_part_lookup", return_value={}):
        response = client.get("/details/not-a-category")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid category"}


def test_dashboard_missing_parts_api_returns_enriched_json(client, collection_records):
    with patch("routes.dashboard.load_part_lookup", return_value={}):
        response = client.get("/api/missing_parts")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["part_num"] == "3001"
    assert payload[0]["total_quantity"] == 10
    assert payload[0]["have_quantity"] == 4


def test_dashboard_missing_minifigure_api_returns_empty_list(client):
    with patch("routes.dashboard.load_part_lookup", return_value={}):
        response = client.get("/api/missing_minifigure_parts")

    assert response.status_code == 200
    assert response.get_json() == []


def test_dashboard_part_image_api_uses_catalog_fallback(client, collection_records):
    part = db.session.get(RebrickableParts, "3001")
    part.part_img_url = "https://example.test/3001.png"
    db.session.commit()

    with patch("routes.dashboard.cache_image", return_value="/cached/3001.png"):
        response = client.get("/api/cache_part_image/3001/1")

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "url": "/cached/3001.png"}


def test_dashboard_part_image_api_returns_default_for_unknown_part(client):
    response = client.get("/api/cache_part_image/unknown/1")

    assert response.status_code == 200
    assert response.get_json() == {
        "success": False,
        "url": "/static/default_image.png",
    }


def test_set_maintenance_script_retains_filter_and_safe_rendering_contracts():
    script = Path("brick_manager/static/js/set_maintenance.js").read_text()

    assert "const escapeHtml" in script
    assert "initSearchAndFilter" in script
    assert "clearAllFilters" in script
    assert "sets-table-main" in script
