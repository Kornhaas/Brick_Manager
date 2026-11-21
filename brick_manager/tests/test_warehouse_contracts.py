"""Physical warehouse contracts exercised through their browser entrypoints."""

from datetime import datetime

import pytest
from models import (
    PartStorage,
    RebrickableColors,
    RebrickablePartCategories,
    RebrickableParts,
    StorageMove,
    StoragePlacement,
    StorageUnit,
    db,
)


def post(client, path, data, expected=201):
    response = client.post("/warehouse" + path, json=data)
    assert response.status_code == expected, response.get_json()
    return response.get_json()


@pytest.fixture
def warehouse_catalog(app):
    db.session.add_all(
        [
            RebrickablePartCategories(id=71, name="Representative Bricks"),
            RebrickableColors(id=17, name="Test color", rgb="112233", is_trans=False),
        ]
    )
    db.session.flush()
    db.session.add(
        RebrickableParts(
            part_num="warehouse-part", name="Representative part", part_cat_id=71
        )
    )
    db.session.commit()


@pytest.fixture
def warehouse_fixture(client, warehouse_catalog):
    zone = post(
        client, "/locations", {"kind": "zone", "label": "Representative active zone"}
    )
    rack = post(
        client,
        "/locations",
        {"kind": "rack", "label": "Example rack", "parent_id": zone["id"]},
    )
    shelf = post(
        client,
        "/locations",
        {"kind": "shelf", "label": "Mixed test compartment", "parent_id": rack["id"]},
    )
    other = post(
        client,
        "/locations",
        {"kind": "shelf", "label": "Alternative compartment", "parent_id": rack["id"]},
    )
    types = post(client, "/setup", {})
    by_name = {item["name"]: item for item in types}
    units = []
    for label in ["3", "4", "6", "6", "9"]:
        unit = post(
            client,
            "/units",
            {"label": label, "type_id": by_name["HMH S"]["id"], "fill_state": "space"},
        )
        units.append(unit)
    for order, unit in enumerate(units):
        post(
            client,
            f"/units/{unit['id']}/placement",
            {"shelf_id": shelf["id"], "order_left": order},
        )
    return {"shelf": shelf, "other": other, "types": by_name, "units": units}


def count_content(client, unit_id, quantity=10):
    row = post(
        client,
        "/contents",
        {
            "part_num": "warehouse-part",
            "color_id": 17,
            "storage_unit_id": unit_id,
            "quantity": None,
        },
    )
    response = client.patch(
        f"/warehouse/contents/{row['id']}",
        json={"quantity": quantity, "reason": "Observed physical inventory count"},
    )
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def test_warehouse_page_exposes_all_connected_flows(client):
    response = client.get("/warehouse")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for text in [
        "Lagerübersicht",
        "/warehouse/intake",
        "/warehouse/reorganize",
        "/warehouse/box-types",
        "/warehouse/locations",
        "/warehouse/capture",
        "/warehouse/settings-page",
        "warehouse.js",
        "warehouse-csrf",
    ]:
        assert text in html
    assert "Lagerverwaltung" in client.get("/").get_data(as_text=True)


def test_warehouse_csrf_rejects_missing_and_accepts_session_token(client, app):
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        response = client.post(
            "/warehouse/locations", json={"kind": "zone", "label": "No token"}
        )
        assert response.status_code == 403
        client.get("/warehouse")
        with client.session_transaction() as current:
            token = current["warehouse_csrf"]
        response = client.post(
            "/warehouse/locations",
            json={"kind": "zone", "label": "Token checked"},
            headers={"X-CSRF-Token": token},
        )
        assert response.status_code == 201
    finally:
        app.config["WTF_CSRF_ENABLED"] = False


def test_snapshot_keeps_duplicate_labels_distinct_and_paths_stable(
    client, warehouse_fixture
):
    data = client.get("/warehouse/data").get_json()
    units = [u for u in data["units"] if u["label"] == "6"]
    assert len(units) == 2
    assert units[0]["id"] != units[1]["id"]
    assert all("Mixed test compartment" in u["address"]["display"] for u in units)
    assert len(data["placements"]) == 5


def test_observed_stack_has_explicit_unverified_status(client, warehouse_fixture):
    types = warehouse_fixture["types"]
    base = warehouse_fixture["units"][0]
    upper = post(client, "/units", {"label": "top", "type_id": types["HMH S"]["id"]})
    response = client.post(
        f"/warehouse/units/{upper['id']}/placement",
        json={"support_unit_id": base["id"], "relation_kind": "stacked"},
    )
    assert response.status_code == 409
    captured = post(
        client,
        f"/units/{upper['id']}/placement",
        {
            "support_unit_id": base["id"],
            "relation_kind": "stacked",
            "observed_unverified": True,
        },
    )
    assert captured["placement"]["support_unit_id"] == base["id"]
    assert captured["placement"]["relation_kind"] == "stacked"
    assert captured["address"]["unit_path"][0]["id"] == base["id"]


def test_mixed_hmh_sizes_cannot_be_observed_as_valid_stack(client, warehouse_fixture):
    base = warehouse_fixture["units"][0]
    upper = post(
        client,
        "/units",
        {"label": "XS", "type_id": warehouse_fixture["types"]["HMH XS"]["id"]},
    )
    response = client.post(
        f"/warehouse/units/{upper['id']}/placement",
        json={
            "support_unit_id": base["id"],
            "relation_kind": "stacked",
            "observed_unverified": True,
        },
    )
    assert response.status_code == 409
    assert db.session.get(StoragePlacement, upper["id"]) is None


def test_loose_cyeer_support_remains_distinct(client, warehouse_fixture):
    lower_type = warehouse_fixture["types"]["CYEER 750 ml"]["id"]
    upper_type = warehouse_fixture["types"]["Feinkost 125 ml"]["id"]
    lower = post(client, "/units", {"label": "CYEER", "type_id": lower_type})
    upper = post(client, "/units", {"label": "cup", "type_id": upper_type})
    post(
        client,
        f"/units/{lower['id']}/placement",
        {"shelf_id": warehouse_fixture["shelf"]["id"], "order_left": 7},
    )
    post(
        client,
        "/stack-rules",
        {
            "lower_type_id": lower_type,
            "upper_type_id": upper_type,
            "relation_kind": "loose_on",
            "verified": True,
        },
    )
    result = post(
        client,
        f"/units/{upper['id']}/placement",
        {"support_unit_id": lower["id"], "relation_kind": "loose_on"},
    )
    assert result["placement"]["relation_kind"] == "loose_on"
    details = client.get(f"/warehouse/units/{lower['id']}").get_json()
    assert details["access_requires_removal"] == [upper["id"]]


@pytest.mark.parametrize(
    ("type_name", "expected_count"), [("STANLEY 1-93-980", 30), ("STANLEY 1-93-978", 9)]
)
def test_magazine_drawers_and_addressable_partitions(
    client, warehouse_fixture, type_name, expected_count
):
    cabinet = post(
        client,
        "/units",
        {"label": "Magazine", "type_id": warehouse_fixture["types"][type_name]["id"]},
    )
    assert len(cabinet["children"]) == expected_count
    drawer = cabinet["children"][0]
    for count in [2, 3, 1]:
        result = post(
            client, f"/units/{drawer['id']}/partitions", {"partition_count": count}, 200
        )
        assert result["partition_count"] == count
        assert len(result["children"]) == (count if count > 1 else 0)
        assert all(
            child["host_unit_id"] == drawer["id"] for child in result["children"]
        )


def test_quantity_transfer_requires_confirmation_and_is_idempotent(
    client, warehouse_fixture
):
    source_unit, target_unit = warehouse_fixture["units"][:2]
    source = count_content(client, source_unit["id"], 10)
    target = count_content(client, target_unit["id"], 2)
    move = post(
        client,
        "/moves",
        {
            "kind": "quantity",
            "storage_id": source["id"],
            "target_unit_id": target_unit["id"],
            "quantity": 4,
            "idempotency_key": "route-transfer",
            "reason": "Move physical Bricks",
        },
    )
    assert db.session.get(PartStorage, source["id"]).quantity == 10
    planned = post(client, f"/moves/{move['id']}/plan", {}, 200)
    assert planned["status"] == "planned"
    assert db.session.get(PartStorage, source["id"]).quantity == 10
    confirm = {
        "revision": planned["revision"],
        "idempotency_key": "route-transfer",
        "capacity_confirmed": True,
        "physical_fit_confirmed": True,
    }
    post(client, f"/moves/{move['id']}/confirm", confirm, 200)
    post(client, f"/moves/{move['id']}/confirm", confirm, 200)
    assert db.session.get(PartStorage, source["id"]).quantity == 6
    assert db.session.get(PartStorage, target["id"]).quantity == 6
    assert StorageMove.query.filter_by(idempotency_key="route-transfer").count() == 1


def test_unit_move_preserves_labels_and_old_address_until_confirmed(
    client, warehouse_fixture
):
    unit = warehouse_fixture["units"][0]
    move = post(
        client,
        "/moves",
        {
            "kind": "unit",
            "unit_id": unit["id"],
            "target_placement": {
                "shelf_id": warehouse_fixture["other"]["id"],
                "order_left": 1,
            },
            "idempotency_key": "unit-to-other",
        },
    )
    planned = post(client, f"/moves/{move['id']}/plan", {}, 200)
    assert (
        db.session.get(StoragePlacement, unit["id"]).shelf_id
        == warehouse_fixture["shelf"]["id"]
    )
    post(
        client,
        f"/moves/{move['id']}/confirm",
        {
            "revision": planned["revision"],
            "physical_fit_confirmed": True,
            "capacity_confirmed": True,
        },
        200,
    )
    assert (
        db.session.get(StoragePlacement, unit["id"]).shelf_id
        == warehouse_fixture["other"]["id"]
    )
    assert [u.label for u in StorageUnit.query.order_by(StorageUnit.id)] == [
        "3",
        "4",
        "6",
        "6",
        "9",
    ]


def test_unknown_history_and_category_default_are_explained(client, warehouse_fixture):
    post(
        client,
        "/category-rules",
        {"category_id": 71, "location_id": warehouse_fixture["shelf"]["id"]},
    )
    response = client.get("/warehouse/parts/warehouse-part/suggestion?color_id=17")
    assert response.status_code == 200
    data = response.get_json()
    assert data["default_location_id"] == warehouse_fixture["shelf"]["id"]
    assert data["demand"]["status"] == "unknown"
    assert data["missing"]
    assert data["classification"] == "keep_accessible"


def test_space_report_does_not_treat_empty_shell_as_free(client, warehouse_fixture):
    unit = warehouse_fixture["units"][0]
    response = client.patch(
        f"/warehouse/units/{unit['id']}", json={"contents_complete": True}
    )
    assert response.status_code == 200
    assert response.get_json()["empty"] is True
    report = client.get(
        f"/warehouse/locations/{warehouse_fixture['shelf']['id']}"
    ).get_json()
    assert report["base_count"] == 5
    assert report["fit_known"] is False
    assert report["free_intervals_mm"] == []
    assert "Leere Behälter" in report["note"]


@pytest.mark.parametrize("payload", [[], None, "text"])
def test_invalid_json_never_creates_location(client, payload):
    response = client.post("/warehouse/locations", json=payload)
    assert response.status_code == 400


def test_invalid_color_filter_is_rejected(client):
    assert client.get("/warehouse/parts/part/locations?color_id=red").status_code == 400


def test_missing_unit_returns_safe_not_found(client):
    response = client.get("/warehouse/units/999999")
    assert response.status_code == 404
    assert "Lagerobjekt" in response.get_json()["error"]


def _http_catalog():
    from models import CatalogGeneration, RebrickableSets

    from brick_manager.tests.test_part_history import catalog_fixture

    catalog_fixture()
    db.session.get(CatalogGeneration, 1).completed_at = datetime.now()
    db.session.get(RebrickableSets, "old-set").year = datetime.now().year - 12
    db.session.get(RebrickableSets, "new-set").year = datetime.now().year
    db.session.commit()


def test_historical_candidates_and_unknown_demand_through_regular_routes(client, app):
    _http_catalog()
    zone = post(client, "/locations", {"kind": "zone", "label": "Historical test zone"})
    rack = post(
        client,
        "/locations",
        {"kind": "rack", "label": "Category rack", "parent_id": zone["id"]},
    )
    shelf = post(
        client,
        "/locations",
        {"kind": "shelf", "label": "History compartment", "parent_id": rack["id"]},
    )
    box = post(
        client,
        "/units",
        {"label": "17", "contents_complete": True, "fill_state": "space"},
    )
    post(client, f"/units/{box['id']}/placement", {"shelf_id": shelf["id"]})
    post(
        client,
        "/contents",
        {"part_num": "old", "color_id": 1, "storage_unit_id": box["id"]},
    )
    client.patch(f"/warehouse/units/{box['id']}", json={"contents_complete": True})
    post(client, "/category-rules", {"category_id": 1, "location_id": rack["id"]})
    old = client.get("/warehouse/parts/old/suggestion?color_id=1").get_json()
    assert old["classification"] == "manual_archive_review"
    assert old["hint"] == "Eigenbedarf unbekannt · bitte prüfen"
    assert old["default_location_id"] == rack["id"]
    assert old["intake_archive_default"] is False
    new = client.get("/warehouse/parts/new/suggestion?color_id=1").get_json()
    assert new["classification"] == "keep_accessible"
    review = client.get(f"/warehouse/locations/{shelf['id']}/suggestions").get_json()
    assert review["units"][0]["whole_box"] is True
    assert review["units"][0]["hint"] == "Eigenbedarf unbekannt · bitte prüfen"
    assert review["units"][0]["effects"]["empty_container_releases_space"] is False


def test_unknown_set_year_is_visible_through_history_route(client, app):
    from models import RebrickableSets

    _http_catalog()
    row = db.session.get(RebrickableSets, "old-set")
    row.year = 0
    db.session.commit()
    history = client.get("/warehouse/parts/old/history?color_id=1").get_json()
    assert history["known_set_count"] == 1
    assert history["last_year"] is None
    assert history["complete"] is False
    assert history["missing"]
    result = client.get("/warehouse/parts/old/suggestion?color_id=1").get_json()
    assert result["classification"] == "keep_accessible"
    assert result["missing"]


def test_physical_unit_labels_use_identity_and_explicit_print_confirmation(
    client, warehouse_fixture, monkeypatch, tmp_path
):
    from config import Config
    from routes import warehouse

    first, second = warehouse_fixture["units"][2:4]
    first_row = count_content(client, first["id"], 4)
    second_row = count_content(client, second["id"], 7)
    seen = []

    def generate(info):
        seen.append(info)
        output = tmp_path / f"label-{len(seen)}.jpg"
        output.write_bytes(b"test-jpg")
        return str(output)

    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setattr(warehouse, "create_box_label_jpg", generate)
    for unit in [first, second]:
        response = client.get(f"/warehouse/units/{unit['id']}/label")
        assert response.status_code == 200
        assert response.data == b"test-jpg"
        assert response.mimetype == "image/jpeg"
        assert str(unit["id"]) in response.headers["Content-Disposition"]
        assert db.session.get(StorageUnit, unit["id"]).label_printed is False
    assert seen[0]["box"] == seen[1]["box"] == "6"
    assert seen[0]["unit_id"] != seen[1]["unit_id"]
    post(client, f"/units/{first['id']}/printed", {}, 200)
    assert db.session.get(StorageUnit, first["id"]).label_printed is True
    assert db.session.get(StorageUnit, second["id"]).label_printed is False
    assert db.session.get(PartStorage, first_row["id"]).quantity == 4
    assert db.session.get(PartStorage, second_row["id"]).quantity == 7


def test_measured_target_preview_and_slope_collision_via_routes(
    client, warehouse_fixture
):
    target = warehouse_fixture["other"]
    type_id = warehouse_fixture["types"]["HMH S"]["id"]
    response = client.patch(
        f"/warehouse/types/{type_id}",
        json={
            "width_mm": 100,
            "depth_mm": 80,
            "height_mm": 60,
            "dimensions_status": "measured",
        },
    )
    assert response.status_code == 200
    response = client.patch(
        f"/warehouse/locations/{target['id']}",
        json={
            "width_mm": 300,
            "depth_mm": 100,
            "height_profile": [[0, 150], [300, 30]],
            "measurement_status": "measured",
        },
    )
    assert response.status_code == 200
    unit = warehouse_fixture["units"][0]
    first = post(
        client,
        f"/units/{unit['id']}/preview",
        {"shelf_id": target["id"], "x_mm": 0, "depth_offset_mm": 0},
        200,
    )
    assert first["status"] == "fits"
    far_right = post(
        client,
        f"/units/{unit['id']}/preview",
        {"shelf_id": target["id"], "x_mm": 200, "depth_offset_mm": 0},
        200,
    )
    assert far_right["status"] == "no_fit"
    assert any(
        "höhe" in reason.lower() or "schräge" in reason.lower()
        for reason in far_right["reasons"]
    )


def test_removing_verified_empty_shell_frees_base_only_after_confirmation(
    client, warehouse_fixture
):
    unit = warehouse_fixture["units"][0]
    client.patch(f"/warehouse/units/{unit['id']}", json={"contents_complete": True})
    move = post(
        client,
        "/moves",
        {
            "kind": "unit",
            "unit_id": unit["id"],
            "target_placement": {"remove": True},
            "idempotency_key": "remove-empty-shell",
        },
    )
    planned = post(client, f"/moves/{move['id']}/plan", {}, 200)
    assert (
        client.get(
            f"/warehouse/locations/{warehouse_fixture['shelf']['id']}"
        ).get_json()["base_count"]
        == 5
    )
    post(client, f"/moves/{move['id']}/confirm", {"revision": planned["revision"]}, 200)
    report = client.get(
        f"/warehouse/locations/{warehouse_fixture['shelf']['id']}"
    ).get_json()
    assert report["base_count"] == 4
    assert db.session.get(StorageUnit, unit["id"]).label == "3"
    assert db.session.get(StoragePlacement, unit["id"]) is None


def test_legacy_unknown_colour_can_be_resolved_before_quantitative_transfer(
    client, warehouse_fixture
):
    source_unit, target_unit = warehouse_fixture["units"][:2]
    unknown = post(
        client,
        "/contents",
        {
            "part_num": "warehouse-part",
            "color_id": None,
            "storage_unit_id": source_unit["id"],
        },
    )
    response = client.patch(
        f"/warehouse/contents/{unknown['id']}",
        json={
            "color_id": 17,
            "quantity": 8,
            "reason": "Physically identified colour and counted existing Bricks",
        },
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["color_id"] == 17
    assert db.session.get(PartStorage, unknown["id"]).color_id == 17
    move = post(
        client,
        "/moves",
        {
            "kind": "quantity",
            "storage_id": unknown["id"],
            "target_unit_id": target_unit["id"],
            "quantity": 3,
            "idempotency_key": "resolved-colour-transfer",
        },
    )
    planned = post(client, f"/moves/{move['id']}/plan", {}, 200)
    post(
        client,
        f"/moves/{move['id']}/confirm",
        {"revision": planned["revision"], "capacity_confirmed": True},
        200,
    )
    assert db.session.get(PartStorage, unknown["id"]).quantity == 5
    assert (
        PartStorage.query.filter_by(
            storage_unit_id=target_unit["id"], part_num="warehouse-part", color_id=17
        )
        .one()
        .quantity
        == 3
    )


def test_warehouse_feature_switch_keeps_mutations_disabled(client, app):
    previous = app.config.get("WAREHOUSE_ENABLED", True)
    app.config["WAREHOUSE_ENABLED"] = False
    try:
        assert client.get("/warehouse").status_code == 404
        assert (
            client.post(
                "/warehouse/locations", json={"kind": "zone", "label": "Disabled"}
            ).status_code
            == 404
        )
        from models import StorageLocation

        assert StorageLocation.query.filter_by(label="Disabled").count() == 0
    finally:
        app.config["WAREHOUSE_ENABLED"] = previous


@pytest.mark.parametrize("configured", [None, "true"])
def test_warehouse_enabled_by_default_or_explicit_true(
    client, app, monkeypatch, configured
):
    import runpy
    from pathlib import Path
    from unittest.mock import patch

    if configured is None:
        monkeypatch.delenv("WAREHOUSE_ENABLED", raising=False)
    else:
        monkeypatch.setenv("WAREHOUSE_ENABLED", configured)
    # Read the real Config without creating runtime directories.
    with patch("os.makedirs"):
        config = runpy.run_path(str(Path(__file__).parents[1] / "config.py"))["Config"]
    monkeypatch.setitem(app.config, "WAREHOUSE_ENABLED", config.WAREHOUSE_ENABLED)
    response = client.get("/warehouse")
    assert response.status_code == 200
    assert b"warehouse-layout" in response.data


def test_initial_shelf_placeholder_and_versioned_script(client):
    import re

    response = client.get("/warehouse")
    html = response.get_data(as_text=True)
    assert (
        '<select id="warehouse-shelf" disabled><option value="">Fach wird geladen'
        in html
    )
    assert re.search(r"js/warehouse\.js\?v=\d+", html)
