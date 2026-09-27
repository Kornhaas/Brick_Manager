"""Contract tests for the authenticated desktop-client API."""

from __future__ import annotations

import pytest
from models import (
    PartStorage,
    RebrickableColors,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    db,
)

API_KEY = "test-client-api-key"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


@pytest.fixture
def part_records(app):
    category = RebrickablePartCategories(name="Brick")
    theme = RebrickableThemes(name="Test theme")
    color = RebrickableColors(id=5, name="Red", rgb="C91A09", is_trans=False)
    db.session.add_all([category, theme, color])
    db.session.flush()

    part = RebrickableParts(
        part_num="3001",
        name="Brick 2 x 4",
        part_cat_id=category.id,
        part_img_url="https://example.test/3001.png",
    )
    template_set = RebrickableSets(
        set_num="10497-1",
        name="Galaxy Explorer",
        year=2022,
        theme_id=theme.id,
        num_parts=1000,
    )
    db.session.add_all([part, template_set])
    db.session.flush()

    user_set = User_Set(set_num=template_set.set_num)
    db.session.add(user_set)
    db.session.flush()
    user_part = User_Parts(
        part_num=part.part_num,
        color_id=color.id,
        quantity=12,
        have_quantity=8,
        user_set_id=user_set.id,
    )
    storage = PartStorage(
        part_num=part.part_num,
        color_id=color.id,
        location="Shelf A",
        level="2",
        box="B-07",
        notes="red parts",
    )
    db.session.add_all([user_part, storage])
    db.session.commit()
    return {"part": part, "user_part": user_part, "storage": storage}


def test_client_api_requires_bearer_key(client):
    response = client.get("/api/v1/parts/3001")
    assert response.status_code == 401


def test_client_api_rejects_wrong_key(client):
    response = client.get(
        "/api/v1/parts/3001", headers={"Authorization": "Bearer incorrect"}
    )
    assert response.status_code == 401


def test_client_api_fails_closed_without_configured_key(app, client):
    app.config["BRICK_MANAGER_CLIENT_API_KEY"] = ""
    response = client.get("/api/v1/parts/3001", headers=HEADERS)
    assert response.status_code == 503
    app.config["BRICK_MANAGER_CLIENT_API_KEY"] = API_KEY


def test_get_part_returns_authoritative_database_record(client, part_records):
    response = client.get("/api/v1/parts/3001", headers=HEADERS)
    assert response.status_code == 200
    assert response.json["name"] == "Brick 2 x 4"
    assert response.json["category_name"] == "Brick"


def test_get_sets_returns_real_missing_quantities(client, part_records):
    response = client.get(
        "/api/v1/parts/3001/sets?color_id=5", headers=HEADERS
    )
    assert response.status_code == 200
    assert response.json["items"] == [
        {
            "part_id": part_records["user_part"].id,
            "user_set_id": part_records["user_part"].user_set_id,
            "set_num": "10497-1",
            "set_name": "Galaxy Explorer",
            "needed": 12,
            "have": 8,
            "missing": 4,
            "color_id": 5,
            "color_name": "Red",
            "color_hex": "C91A09",
        }
    ]


def test_get_storage_returns_server_location_fields(client, part_records):
    response = client.get(
        "/api/v1/parts/3001/storage?color_id=5", headers=HEADERS
    )
    assert response.status_code == 200
    item = response.json["items"][0]
    assert (item["location"], item["level"], item["box"]) == ("Shelf A", "2", "B-07")


def test_update_quantity_is_validated_and_clamped(client, part_records):
    invalid = client.put(
        f"/api/v1/user-parts/{part_records['user_part'].id}/quantity",
        headers=HEADERS,
        json={"have_quantity": -1},
    )
    assert invalid.status_code == 400

    response = client.put(
        f"/api/v1/user-parts/{part_records['user_part'].id}/quantity",
        headers=HEADERS,
        json={"have_quantity": 100},
    )
    assert response.status_code == 200
    assert response.json["have_quantity"] == 12
    assert response.json["missing"] == 0


def test_update_storage_writes_server_database(client, part_records):
    response = client.put(
        "/api/v1/parts/3001/storage",
        headers=HEADERS,
        json={"color_id": 5, "location": "Shelf C", "level": "1", "box": "C-02"},
    )
    assert response.status_code == 200
    assert response.json["location"] == "Shelf C"

    stored = db.session.get(PartStorage, part_records["storage"].id)
    assert stored.location == "Shelf C"
    assert stored.box == "C-02"


def test_update_storage_rejects_non_string_fields(client, part_records):
    response = client.put(
        "/api/v1/parts/3001/storage",
        headers=HEADERS,
        json={"location": ["not", "a", "string"]},
    )
    assert response.status_code == 400


def test_invalid_color_filter_is_rejected(client):
    response = client.get(
        "/api/v1/parts/3001/sets?color_id=red", headers=HEADERS
    )
    assert response.status_code == 400
