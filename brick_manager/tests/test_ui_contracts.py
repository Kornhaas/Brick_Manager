"""Server-rendered and JavaScript UI contracts for collection workflows."""

from pathlib import Path
from unittest.mock import patch

import pytest
from flask import render_template
from models import (
    CollectionSnapshot,
    RebrickableColors,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    db,
)
from sqlalchemy import event


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
    assert b"Collection intelligence" in response.data
    assert b'Parts owned</div><div class="metric-value">5</div>' in response.data
    assert (
        b'Parts still missing</div><div class="metric-value">8</div>' in response.data
    )
    assert b"Missing spares</small>" in response.data
    assert b"Konvolut parts owned</span><strong>1</strong>" in response.data
    assert b"Missing Konvolut parts</span><strong>2</strong>" in response.data
    assert b'id="collectionTrend"' in response.data
    assert b'id="historyData"' in response.data
    assert b'id="statusData"' in response.data
    assert b"/static/css/dashboard.css" in response.data
    assert b"/static/js/dashboard.js" in response.data


def test_dashboard_daily_snapshot_is_idempotent_and_refreshes(
    client, collection_records
):
    first_response = client.get("/dashboard")
    part = User_Parts.query.filter_by(user_set_id=collection_records.id).one()
    part.have_quantity = 7
    db.session.commit()
    second_response = client.get("/dashboard")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    snapshots = CollectionSnapshot.query.all()
    assert len(snapshots) == 1
    assert snapshots[0].owned_parts == 8
    assert snapshots[0].missing_parts == 5


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
    assert b'loading="lazy"' in response.data
    assert b'decoding="async"' in response.data
    assert b"document.addEventListener('DOMContentLoaded'" in response.data
    assert b"window.addEventListener('load'" not in response.data
    assert b"Sets with missing parts" in response.data


def test_set_maintenance_template_tolerates_legacy_route_context(app):
    """Template reloads must not fail while an older route remains in memory."""
    with app.test_request_context("/set_maintain"):
        html = render_template("set_maintain.html", sets_with_completeness=[])

    assert "Collection overview" in html
    assert "0 matching sets" in html


def test_set_maintenance_query_count_does_not_grow_per_set(client, collection_records):
    """Loading minifigure parts must not issue one query for every user set."""
    select_counts = []

    def count_selects(_connection, _cursor, statement, *_args):
        if statement.lstrip().upper().startswith("SELECT"):
            select_counts[-1] += 1

    event.listen(db.engine, "before_cursor_execute", count_selects)
    try:
        select_counts.append(0)
        first_response = client.get("/set_maintain")

        db.session.add(User_Set(set_num=collection_records.set_num, status="unknown"))
        db.session.commit()

        select_counts.append(0)
        second_response = client.get("/set_maintain")
    finally:
        event.remove(db.engine, "before_cursor_execute", count_selects)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert select_counts[1] == select_counts[0]


def test_set_maintenance_filters_by_box_and_missing_parts(client, collection_records):
    active_part = User_Parts.query.filter_by(user_set_id=collection_records.id).one()
    active_part.have_quantity = active_part.quantity
    db.session.commit()

    box_response = client.get(
        "/set_maintain", query_string={"box_id": collection_records.id}
    )
    missing_response = client.get(
        "/set_maintain", query_string={"completion": "incomplete"}
    )

    assert box_response.status_code == 200
    assert b"Explorer &amp; Research" in box_response.data
    assert b"Loose Bricks" not in box_response.data
    assert missing_response.status_code == 200
    assert b"Explorer &amp; Research" not in missing_response.data
    assert b"Loose Bricks" in missing_response.data
    assert b"Only sets with missing parts" in missing_response.data


def test_set_maintenance_paginates_large_collections(client, collection_records):
    db.session.add_all(
        [
            User_Set(set_num=collection_records.set_num, status="unknown")
            for _ in range(30)
        ]
    )
    db.session.commit()

    response = client.get("/set_maintain", query_string={"per_page": 25})

    assert response.status_code == 200
    assert response.data.count(b'class="set-row"') == 25
    assert b'aria-label="Set result pages"' in response.data
    assert b"32 matching sets" in response.data


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
