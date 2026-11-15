"""Warehouse archive/intake decisions preserve unknown demand and exact variants."""

from datetime import date

import pytest
from models import (
    PartStorage,
    RebrickableInventoryParts,
    RebrickableSets,
    StorageLocation,
    StoragePlacement,
    StorageUnit,
    User_Parts,
    User_Set,
    db,
)
from services.storage_suggestion_service import (
    MANUAL_REVIEW_HINT,
    archive_suggestions,
    classify_variant,
    get_settings,
    intake_suggestion,
    part_demand,
    save_category_rule,
    save_planned_set,
    save_preference,
    save_settings,
    update_planned_set,
)
from werkzeug.exceptions import BadRequest

from brick_manager.tests.test_part_history import catalog_fixture

TODAY = date(2026, 11, 15)


@pytest.fixture
def warehouse(app):
    catalog_fixture()
    zone = StorageLocation(kind="zone", label="Active", zone_kind="active")
    archive = StorageLocation(kind="zone", label="Archive", zone_kind="archive")
    db.session.add_all([zone, archive])
    db.session.flush()
    rack = StorageLocation(kind="rack", label="Test rack", parent_id=zone.id)
    archive_rack = StorageLocation(
        kind="rack", label="Archive rack", parent_id=archive.id
    )
    db.session.add_all([rack, archive_rack])
    db.session.flush()
    shelf = StorageLocation(
        kind="shelf", label="Representative shelf", parent_id=rack.id
    )
    archive_shelf = StorageLocation(
        kind="shelf", label="Archive shelf", parent_id=archive_rack.id
    )
    db.session.add_all([shelf, archive_shelf])
    db.session.flush()
    active_box = StorageUnit(
        label="6", kind="container", fill_state="space", contents_complete=True
    )
    archived_box = StorageUnit(
        label="6", kind="container", fill_state="space", contents_complete=True
    )
    db.session.add_all([active_box, archived_box])
    db.session.flush()
    db.session.add_all(
        [
            StoragePlacement(unit_id=active_box.id, shelf_id=shelf.id),
            StoragePlacement(unit_id=archived_box.id, shelf_id=archive_shelf.id),
            PartStorage(
                part_num="old", color_id=1, storage_unit_id=active_box.id, quantity=10
            ),
            PartStorage(
                part_num="old", color_id=1, storage_unit_id=archived_box.id, quantity=20
            ),
        ]
    )
    db.session.commit()
    save_category_rule(
        {
            "category_id": 1,
            "location_id": rack.id,
            "archive_location_id": archive_rack.id,
        }
    )
    return {
        "rack": rack.id,
        "shelf": shelf.id,
        "archive": archive.id,
        "archive_rack": archive_rack.id,
        "active_box": active_box.id,
        "archived_box": archived_box.id,
    }


def test_old_rare_unknown_demand_shown_for_manual_review_in_v1(warehouse):
    result = classify_variant("old", 1, TODAY)
    assert result["classification"] == "manual_archive_review"
    assert result["hint"] == "Eigenbedarf unbekannt · bitte prüfen"
    assert result["demand"]["status"] == "unknown"
    suggestions = archive_suggestions(warehouse["shelf"], TODAY)
    unit = suggestions["units"][0]
    assert unit["whole_box"] is True
    assert unit["manual_review"] is True
    assert unit["hint"] == MANUAL_REVIEW_HINT
    assert unit["executable"] is False


def test_unknown_demand_intake_keeps_category_regal_even_with_archive_stock(warehouse):
    result = intake_suggestion("old", 1, TODAY)
    assert result["default_location_id"] == warehouse["rack"]
    assert result["target_unit_id"] == warehouse["active_box"]
    assert result["intake_archive_default"] is False
    archived = next(
        r
        for r in result["existing_locations"]
        if r["unit_id"] == warehouse["archived_box"]
    )
    assert archived["eligible"] is False
    assert PartStorage.query.count() == 2


def test_new_variants_remain_accessible_and_incomplete_years_explain_missing(warehouse):
    result = classify_variant("new", 1, TODAY)
    assert result["classification"] == "keep_accessible"
    assert "aktuell" in result["reasons"][0]
    db.session.get(RebrickableSets, "old-set").year = 0
    db.session.commit()
    result = intake_suggestion("old", 1, TODAY)
    assert result["classification"] == "keep_accessible"
    assert result["default_location_id"] == warehouse["rack"]
    assert "Set-Jahr fehlt oder ist unplausibel" in result["missing"]


def test_mixed_box_is_partial_not_whole_archive_suggestion(warehouse):
    db.session.add(
        PartStorage(
            part_num="new",
            color_id=1,
            quantity=1,
            storage_unit_id=warehouse["active_box"],
        )
    )
    db.session.commit()
    result = archive_suggestions(warehouse["shelf"], TODAY)["units"][0]
    assert result["whole_box"] is False
    assert len(result["eligible_storage_ids"]) == 1
    assert len(result["contents"]) == 2
    assert "Teilumbuchung" in result["reasons"][0]
    db.session.get(StorageUnit, warehouse["active_box"]).contents_complete = False
    db.session.commit()
    assert (
        archive_suggestions(warehouse["shelf"], TODAY)["units"][0]["whole_box"] is False
    )


def test_planned_sets_protect_variant_and_changes_invalidate_review(warehouse):
    plan = save_planned_set({"set_num": "old-set", "quantity": 2})
    save_settings({"planning_reviewed": True})
    demand = part_demand("old", 1, TODAY)
    assert demand["status"] == "positive"
    assert demand["planned_quantity"] == 6  # latest version has three, not 5+3+spares
    assert classify_variant("old", 1, TODAY)["classification"] == "keep_accessible"
    update_planned_set(plan["id"], {"active": False})
    assert get_settings()["planning_reviewed"] is False
    assert part_demand("old", 1, TODAY)["status"] == "unknown"
    save_settings({"planning_reviewed": True})
    assert classify_variant("old", 1, TODAY)["classification"] == "archive_candidate"


def test_existing_open_user_set_demand_prevents_archiving(warehouse):
    user_set = User_Set(set_num="old-set", status="missingparts")
    db.session.add(user_set)
    db.session.flush()
    db.session.add(
        User_Parts(
            part_num="old",
            color_id=1,
            quantity=3,
            have_quantity=1,
            user_set_id=user_set.id,
        )
    )
    db.session.commit()
    assert part_demand("old", 1, TODAY)["open_quantity"] == 2
    assert classify_variant("old", 1, TODAY)["classification"] == "keep_accessible"


def test_missing_planned_inventory_is_unknown_not_zero(warehouse):
    save_planned_set({"set_num": "old-set"})
    RebrickableInventoryParts.query.filter_by(inventory_id=1).delete()
    RebrickableInventoryParts.query.filter_by(inventory_id=2).delete()
    db.session.commit()
    save_settings({"planning_reviewed": True})
    result = part_demand("old", 1, TODAY)
    assert result["status"] == "unknown"
    assert "Geplantes Inventar ohne erfassten Inhalt" in result["missing"]


def test_full_target_fallback_and_manual_preference(warehouse):
    db.session.get(StorageUnit, warehouse["active_box"]).fill_state = "full"
    db.session.commit()
    result = intake_suggestion("old", 1, TODAY)
    assert result["target_unit_id"] is None
    assert result["default_location_id"] == warehouse["rack"]
    save_preference(
        {
            "part_num": "old",
            "color_id": 1,
            "keep_accessible": True,
            "replenishment_unlikely": True,
        }
    )
    result = classify_variant("old", 1, TODAY)
    assert result["classification"] == "keep_accessible"
    assert "Nachschub unwahrscheinlich" in result["reasons"][-1]


def test_settings_validate_flags_and_do_not_expose_secret_config(warehouse):
    from models import ConfigSettings

    db.session.add(ConfigSettings(key="token", value="private", encrypted=True))
    db.session.commit()
    with pytest.raises(BadRequest):
        save_settings({"max_known_sets": True})
    with pytest.raises(BadRequest):
        save_settings({"token": "other"})
    assert "private" not in str(get_settings())
    save_settings(
        {"max_known_sets": 1, "min_age_years": 13, "catalog_max_age_days": 90}
    )
    assert classify_variant("old", 1, TODAY)["classification"] == "keep_accessible"


def test_regular_warehouse_entrypoints_explain_manual_review_and_intake_default(
    warehouse, client
):
    response = client.get("/warehouse/parts/old/suggestion?color_id=1")
    assert response.status_code == 200
    result = response.get_json()
    assert result["hint"] == MANUAL_REVIEW_HINT
    assert result["default_location_id"] == warehouse["rack"]
    assert result["target_unit_id"] == warehouse["active_box"]
    archive = client.get(f"/warehouse/locations/{warehouse['shelf']}/suggestions")
    assert archive.status_code == 200
    unit = archive.get_json()["units"][0]
    assert unit["whole_box"] is True
    assert unit["effects"]["empty_container_releases_space"] is False
    assert unit["effects"]["contiguous_space_verified"] is False
    history = client.get("/warehouse/parts/old/history?color_id=1")
    assert history.status_code == 200
    assert history.get_json()["known_set_count"] == 1


def test_regular_warehouse_configuration_entrypoints(warehouse, client):
    response = client.post(
        "/warehouse/planned-sets", json={"set_num": "old-set", "quantity": 2}
    )
    assert response.status_code == 201
    plan_id = response.get_json()["id"]
    assert (
        client.post("/warehouse/settings", json={"planning_reviewed": True}).status_code
        == 200
    )
    protected = client.get("/warehouse/parts/old/suggestion?color_id=1").get_json()
    assert protected["classification"] == "keep_accessible"
    assert protected["demand"]["planned_quantity"] == 6
    response = client.patch(
        f"/warehouse/planned-sets/{plan_id}", json={"active": False}
    )
    assert response.status_code == 200
    settings = client.get("/warehouse/settings").get_json()
    assert settings["planning_reviewed"] is False
    assert (
        client.post(
            "/warehouse/settings", json={"planning_reviewed": "true"}
        ).status_code
        == 400
    )


def test_supported_box_is_blocker_not_promise_of_free_floor(warehouse):
    upper = StorageUnit(
        label="9", kind="container", fill_state="space", contents_complete=True
    )
    db.session.add(upper)
    db.session.flush()
    db.session.add(
        StoragePlacement(
            unit_id=upper.id,
            support_unit_id=warehouse["active_box"],
            relation_kind="loose_on",
        )
    )
    db.session.commit()
    result = archive_suggestions(warehouse["shelf"], TODAY)
    base = next(
        row for row in result["units"] if row["unit_id"] == warehouse["active_box"]
    )
    assert base["whole_box"] is False
    assert base["supporting_unit_ids"] == [upper.id]
    assert base["effects"]["base_area_if_removed"] is False
    assert base["executable"] is False


def test_planned_subsets_multiply_quantities_without_summing_versions(warehouse):
    from models import RebrickableInventorySets

    db.session.add(
        RebrickableInventorySets(inventory_id=3, set_num="old-set", quantity=2)
    )
    db.session.commit()
    save_planned_set({"set_num": "new-set", "quantity": 3})
    save_settings({"planning_reviewed": True})
    old = part_demand("old", 1, TODAY)
    new = part_demand("new", 1, TODAY)
    assert old["planned_quantity"] == 18  # 3 projects * 2 child sets * 3 latest parts
    assert new["planned_quantity"] == 6
    assert old["versions"][0]["version"] == 1


def test_history_threshold_year_boundary_and_custom_set_limit(warehouse):
    row = db.session.get(RebrickableSets, "old-set")
    row.year = 2016
    db.session.commit()
    assert (
        classify_variant("old", 1, TODAY)["classification"] == "manual_archive_review"
    )
    row.year = 2017
    db.session.commit()
    assert classify_variant("old", 1, TODAY)["classification"] == "keep_accessible"
