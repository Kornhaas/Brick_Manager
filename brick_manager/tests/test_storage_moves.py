"""Confirmed movement preserves physical stock, identities and actual occupied area."""

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
from services.storage_move_service import (
    cancel_move,
    confirm_move,
    create_move,
    plan_move,
)
from services.storage_service import (
    create_location,
    create_type,
    create_unit,
    place_unit,
    save_stack_rule,
    space_report,
    unit_address,
    update_content,
    update_unit,
)
from werkzeug.exceptions import BadRequest, Conflict


@pytest.fixture
def stock(app):
    zone = create_location({"kind": "zone", "label": "Testlager"})
    rack = create_location({"kind": "rack", "label": "T", "parent_id": zone["id"]})
    shelves = [
        create_location(
            {
                "kind": "shelf",
                "label": label,
                "parent_id": rack["id"],
                "width_mm": 600,
                "depth_mm": 300,
                "height_profile": [[0, 1000], [600, 1000]],
                "measurement_status": "measured",
            }
        )
        for label in ("Quellfach", "Zielfach")
    ]
    ctype = create_type(
        {
            "name": "Testbox",
            "width_mm": 100,
            "depth_mm": 100,
            "height_mm": 50,
            "dimensions_status": "measured",
        }
    )
    units = [
        create_unit(
            {
                "label": label,
                "type_id": ctype["id"],
                "fill_state": "space",
                "contents_complete": True,
            }
        )
        for label in ("3", "6", "9")
    ]
    for index, unit in enumerate(units):
        place_unit(
            unit["id"],
            {"shelf_id": shelves[0]["id"], "x_mm": index * 100, "depth_offset_mm": 0},
        )
    db.session.add(RebrickablePartCategories(id=1, name="Bricks"))
    db.session.add(RebrickableParts(part_num="p", name="Part", part_cat_id=1))
    db.session.add(RebrickableColors(id=1, name="Red", rgb="FF0000", is_trans=False))
    db.session.flush()
    source = PartStorage(
        part_num="p",
        color_id=1,
        storage_unit_id=units[0]["id"],
        quantity=10,
        migration_status="confirmed",
    )
    target = PartStorage(
        part_num="p",
        color_id=1,
        storage_unit_id=units[1]["id"],
        quantity=2,
        migration_status="confirmed",
    )
    db.session.add_all([source, target])
    db.session.commit()
    return {
        "shelves": shelves,
        "type": ctype,
        "units": units,
        "source": source.id,
        "target": target.id,
    }


def _transfer(stock, quantity=4, key="transfer", target=None):
    return create_move(
        {
            "kind": "quantity",
            "idempotency_key": key,
            "reason": "Teilmenge umlagern",
            "storage_id": stock["source"],
            "target_unit_id": target or stock["units"][1]["id"],
            "quantity": quantity,
        }
    )


def _quantities(stock):
    return (
        db.session.get(PartStorage, stock["source"]).quantity,
        db.session.get(PartStorage, stock["target"]).quantity,
    )


def test_quantity_move_is_ineffective_until_confirmation_and_idempotent(stock):
    move = _transfer(stock)
    assert move["status"] == "draft"
    assert _quantities(stock) == (10, 2)
    planned = plan_move(move["id"])
    assert _quantities(stock) == (10, 2)
    assert planned["preview"][0]["base_area_released"] is False
    result = confirm_move(
        move["id"], {"revision": planned["revision"], "idempotency_key": "transfer"}
    )
    assert result["status"] == "confirmed"
    assert _quantities(stock) == (6, 6)
    assert sum(_quantities(stock)) == 12
    again = confirm_move(move["id"], {"idempotency_key": "transfer"})
    assert again["revision"] == result["revision"]
    assert _quantities(stock) == (6, 6)
    assert StorageMove.query.count() == 1
    with pytest.raises(Conflict, match="anderen Auftrag"):
        confirm_move(move["id"], {"idempotency_key": "wrong"})


@pytest.mark.parametrize("quantity", [0, -1, True, "4", None])
def test_invalid_transfer_quantities_never_change_stock(stock, quantity):
    with pytest.raises(BadRequest):
        _transfer(stock, quantity)
    db.session.rollback()
    assert _quantities(stock) == (10, 2)
    assert StorageMove.query.count() == 0


def test_excessive_amount_and_reservation_conflicts(stock):
    excessive = _transfer(stock, quantity=11, key="too-many")
    with pytest.raises(Conflict, match="Nicht genügend"):
        plan_move(excessive["id"])
    db.session.rollback()
    first = _transfer(stock, quantity=7, key="first")
    plan_move(first["id"])
    second = _transfer(stock, quantity=7, key="second", target=stock["units"][2]["id"])
    with pytest.raises(Conflict, match="reserviert"):
        plan_move(second["id"])
    db.session.rollback()
    with pytest.raises(Conflict, match="reserviert"):
        update_content(stock["source"], {"quantity": 8, "reason": "Zählung"})
    db.session.rollback()
    cancel_move(first["id"])
    assert plan_move(second["id"])["status"] == "planned"
    assert _quantities(stock) == (10, 2)


def test_external_changes_make_planned_move_stale(stock):
    move = _transfer(stock)
    plan_move(move["id"])
    source = db.session.get(PartStorage, stock["source"])
    source.quantity = 9
    source.revision += 1
    db.session.commit()
    with pytest.raises(Conflict, match="geändert"):
        confirm_move(move["id"])
    db.session.rollback()
    assert _quantities(stock) == (9, 2)
    assert db.session.get(StorageMove, move["id"]).status == "planned"


def test_wrong_revision_or_reused_key_does_not_book_twice(stock):
    move = _transfer(stock)
    with pytest.raises(Conflict, match="anderen Auftrag"):
        _transfer(stock, quantity=5)
    db.session.rollback()
    plan_move(move["id"])
    with pytest.raises(Conflict, match="veraltet"):
        confirm_move(move["id"], {"revision": 99})
    db.session.rollback()
    assert _quantities(stock) == (10, 2)


def test_unknown_source_or_target_must_be_counted_before_transfer(stock):
    source = db.session.get(PartStorage, stock["source"])
    source.quantity = None
    db.session.commit()
    with pytest.raises(Conflict, match="zählen"):
        _transfer(stock)
    db.session.rollback()
    source = db.session.get(PartStorage, stock["source"])
    source.quantity = 10
    target = db.session.get(PartStorage, stock["target"])
    target.quantity = None
    db.session.commit()
    move = _transfer(stock)
    with pytest.raises(Conflict, match="zählen"):
        plan_move(move["id"])
    db.session.rollback()
    assert _quantities(stock) == (10, None)


def test_capacity_and_full_target_checks_require_explicit_confirmation(stock):
    target_id = stock["units"][1]["id"]
    update_unit(target_id, {"fill_state": "full"})
    move = _transfer(stock)
    with pytest.raises(Conflict, match="voll"):
        plan_move(move["id"])
    db.session.rollback()
    update_unit(target_id, {"fill_state": "nearly_full"})
    plan_move(move["id"])
    with pytest.raises(Conflict, match="Zielkapazität"):
        confirm_move(move["id"])
    db.session.rollback()
    confirm_move(move["id"], {"capacity_confirmed": True})
    assert _quantities(stock) == (6, 6)


def test_emptying_box_does_not_free_ground_until_shell_is_removed(stock):
    before = space_report(stock["shelves"][0]["id"])
    move = _transfer(stock, quantity=10)
    planned = plan_move(move["id"])
    effect = planned["preview"][0]
    assert effect["container_emptied"] is True
    assert effect["stack_lowered"] is False
    assert effect["base_area_released"] is False
    confirm_move(move["id"])
    assert (
        space_report(stock["shelves"][0]["id"])["free_intervals_mm"]
        == before["free_intervals_mm"]
    )
    shell = create_move(
        {
            "kind": "unit",
            "idempotency_key": "remove-shell",
            "unit_id": stock["units"][0]["id"],
            "target_placement": {"remove": True},
        }
    )
    planned_shell = plan_move(shell["id"])
    assert planned_shell["preview"][0]["base_area_released"] is True
    confirm_move(shell["id"])
    after = space_report(stock["shelves"][0]["id"])
    assert after["base_count"] == before["base_count"] - 1
    assert [0, 100] in after["free_intervals_mm"]
    assert [unit.label for unit in StorageUnit.query.order_by(StorageUnit.id)] == [
        "3",
        "6",
        "9",
    ]
    assert db.session.get(PartStorage, stock["source"]).quantity == 0


def test_whole_box_moves_with_contents_only_after_confirmation(stock):
    unit = stock["units"][0]
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "whole",
            "unit_id": unit["id"],
            "target_placement": {
                "shelf_id": stock["shelves"][1]["id"],
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        }
    )
    plan_move(move["id"])
    assert unit_address(unit["id"])["shelf_id"] == stock["shelves"][0]["id"]
    assert _quantities(stock) == (10, 2)
    confirm_move(move["id"])
    assert unit_address(unit["id"])["shelf_id"] == stock["shelves"][1]["id"]
    assert _quantities(stock) == (10, 2)
    assert db.session.get(StorageUnit, unit["id"]).label == "3"
    assert db.session.get(PartStorage, stock["source"]).storage_unit_id == unit["id"]


def test_removing_upper_container_lowers_stack_but_not_base_area(stock):
    lower = stock["units"][0]
    upper = create_unit(
        {"label": "4", "type_id": stock["type"]["id"], "contents_complete": True}
    )
    save_stack_rule(
        {
            "lower_type_id": stock["type"]["id"],
            "upper_type_id": stock["type"]["id"],
            "verified": True,
            "height_increment_mm": 40,
        }
    )
    place_unit(upper["id"], {"support_unit_id": lower["id"], "depth_offset_mm": 0})
    before = space_report(stock["shelves"][0]["id"])
    blocked = create_move(
        {
            "kind": "unit",
            "idempotency_key": "lower-blocked",
            "unit_id": lower["id"],
            "target_placement": {
                "shelf_id": stock["shelves"][1]["id"],
                "x_mm": 100,
                "depth_offset_mm": 0,
            },
        }
    )
    with pytest.raises(Conflict, match="Aufliegende"):
        plan_move(blocked["id"])
    db.session.rollback()
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "upper",
            "unit_id": upper["id"],
            "target_placement": {
                "shelf_id": stock["shelves"][1]["id"],
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        }
    )
    preview = plan_move(move["id"])["preview"][0]
    assert preview["stack_lowered"] is True
    assert preview["base_area_released"] is False
    confirm_move(move["id"])
    assert (
        space_report(stock["shelves"][0]["id"])["free_intervals_mm"]
        == before["free_intervals_mm"]
    )
    assert unit_address(lower["id"])["shelf_id"] == stock["shelves"][0]["id"]


def test_new_intake_and_followup_moves_are_independent_confirmed_steps(stock):
    target = stock["units"][2]["id"]
    intake = create_move(
        {
            "kind": "intake",
            "idempotency_key": "intake",
            "part_num": "p",
            "color_id": 1,
            "quantity": 5,
            "target_unit_id": target,
        }
    )
    follow = create_move(
        {
            "kind": "unit",
            "idempotency_key": "follow",
            "depends_on_move_id": intake["id"],
            "unit_id": target,
            "target_placement": {
                "shelf_id": stock["shelves"][1]["id"],
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        }
    )
    with pytest.raises(Conflict, match="Vorausgehende"):
        plan_move(follow["id"])
    db.session.rollback()
    plan_move(intake["id"])
    assert PartStorage.query.filter_by(storage_unit_id=target).count() == 0
    confirm_move(intake["id"])
    confirm_move(intake["id"])
    assert PartStorage.query.filter_by(storage_unit_id=target).one().quantity == 5
    plan_move(follow["id"])
    cancel_move(follow["id"])
    assert db.session.get(StorageMove, intake["id"]).status == "confirmed"
    assert (
        db.session.get(StoragePlacement, target).shelf_id == stock["shelves"][0]["id"]
    )


def test_noop_placement_does_not_claim_new_free_ground(stock):
    unit_id = stock["units"][0]["id"]
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "noop",
            "unit_id": unit_id,
            "target_placement": {
                "shelf_id": stock["shelves"][0]["id"],
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        }
    )
    preview = plan_move(move["id"])["preview"][0]
    assert preview["base_area_released"] is False
    before = space_report(stock["shelves"][0]["id"])
    result = confirm_move(move["id"])
    assert (
        result["snapshot"]["space_after"][str(stock["shelves"][0]["id"])][
            "free_intervals_mm"
        ]
        == before["free_intervals_mm"]
    )


def test_target_shelf_is_in_confirmed_space_effects(stock):
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "target-effects",
            "unit_id": stock["units"][0]["id"],
            "target_placement": {
                "shelf_id": stock["shelves"][1]["id"],
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        }
    )
    plan_move(move["id"])
    result = confirm_move(move["id"])
    target_id = str(stock["shelves"][1]["id"])
    assert result["snapshot"]["space_before"][target_id]["base_count"] == 0
    assert result["snapshot"]["space_after"][target_id]["base_count"] == 1


def test_cabinet_with_occupied_drawer_cannot_be_removed_as_empty_shell(stock):
    ctype = create_type(
        {"name": "Two-drawer cabinet", "kind": "cabinet", "drawer_count": 2}
    )
    cabinet = create_unit(
        {"label": "Magazin", "type_id": ctype["id"], "contents_complete": True}
    )
    place_unit(cabinet["id"], {"shelf_id": stock["shelves"][1]["id"]})
    drawer = cabinet["children"][0]
    db.session.add(
        PartStorage(part_num="p", color_id=1, quantity=3, storage_unit_id=drawer["id"])
    )
    db.session.commit()
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "cabinet-shell",
            "unit_id": cabinet["id"],
            "target_placement": {"remove": True},
        }
    )
    with pytest.raises(Conflict, match="leere"):
        plan_move(move["id"])
    db.session.rollback()
    assert db.session.get(StoragePlacement, cabinet["id"]) is not None
    assert PartStorage.query.filter_by(storage_unit_id=drawer["id"]).one().quantity == 3


def test_two_database_sessions_cannot_reserve_same_quantity(stock, tmp_path):
    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from flask import Flask

    first = _transfer(stock, quantity=7, key="concurrent-1")
    second = _transfer(
        stock, quantity=7, key="concurrent-2", target=stock["units"][2]["id"]
    )
    # Copy only the test database, then give each worker a distinct scoped session.
    db.session.remove()
    file_path = tmp_path / "concurrent.db"
    raw = db.engine.raw_connection()
    destination = sqlite3.connect(file_path)
    try:
        raw.driver_connection.backup(destination)
    finally:
        destination.close()
        raw.close()
    application = Flask("storage-concurrency-test")
    application.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{file_path}"
    db.init_app(application)
    barrier = Barrier(2)

    def reserve(identifier):
        with application.app_context():
            barrier.wait(timeout=10)
            try:
                plan_move(identifier)
                return "planned"
            except Conflict:
                db.session.rollback()
                return "conflict"
            finally:
                db.session.remove()

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = list(workers.map(reserve, [first["id"], second["id"]]))
        assert sorted(outcomes) == ["conflict", "planned"]
        with application.app_context():
            assert StorageMove.query.filter_by(status="planned").count() == 1
            assert db.session.get(PartStorage, stock["source"]).quantity == 10
            db.session.remove()
            db.engine.dispose()
    finally:
        with application.app_context():
            db.session.remove()
            db.engine.dispose()


def test_batch_cannot_place_two_units_on_same_target_footprint(stock):
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "overlapping-batch",
            "items": [
                {
                    "unit_id": stock["units"][0]["id"],
                    "target_placement": {
                        "shelf_id": stock["shelves"][1]["id"],
                        "x_mm": 0,
                        "depth_offset_mm": 0,
                    },
                },
                {
                    "unit_id": stock["units"][1]["id"],
                    "target_placement": {
                        "shelf_id": stock["shelves"][1]["id"],
                        "x_mm": 0,
                        "depth_offset_mm": 0,
                    },
                },
            ],
        }
    )
    with pytest.raises(Conflict):
        plan_move(move["id"])
    db.session.rollback()
    assert (
        db.session.get(StoragePlacement, stock["units"][0]["id"]).shelf_id
        == stock["shelves"][0]["id"]
    )
    assert (
        db.session.get(StoragePlacement, stock["units"][1]["id"]).shelf_id
        == stock["shelves"][0]["id"]
    )


def test_one_physical_unit_cannot_have_two_destinations_in_one_move(stock):
    with pytest.raises((BadRequest, Conflict)):
        move = create_move(
            {
                "kind": "unit",
                "idempotency_key": "duplicate-unit",
                "items": [
                    {
                        "unit_id": stock["units"][0]["id"],
                        "target_placement": {
                            "shelf_id": stock["shelves"][1]["id"],
                            "x_mm": 0,
                            "depth_offset_mm": 0,
                        },
                    },
                    {
                        "unit_id": stock["units"][0]["id"],
                        "target_placement": {
                            "shelf_id": stock["shelves"][1]["id"],
                            "x_mm": 200,
                            "depth_offset_mm": 0,
                        },
                    },
                ],
            }
        )
        plan_move(move["id"])
    db.session.rollback()
    assert (
        db.session.get(StoragePlacement, stock["units"][0]["id"]).shelf_id
        == stock["shelves"][0]["id"]
    )


def test_support_rule_change_cannot_silently_confirm_stale_geometry(stock):
    type_id = stock["type"]["id"]
    rule = save_stack_rule(
        {
            "lower_type_id": type_id,
            "upper_type_id": type_id,
            "verified": True,
            "height_increment_mm": 40,
        }
    )
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "rule-stale",
            "unit_id": stock["units"][2]["id"],
            "target_placement": {
                "support_unit_id": stock["units"][0]["id"],
                "depth_offset_mm": 0,
            },
        }
    )
    plan_move(move["id"])
    # Either editing a reserved rule is rejected, or confirming its old plan is.
    with pytest.raises(Conflict):
        save_stack_rule(
            {
                "id": rule["id"],
                "lower_type_id": type_id,
                "upper_type_id": type_id,
                "verified": True,
                "height_increment_mm": 45,
            }
        )
        confirm_move(move["id"], {"physical_fit_confirmed": True})
    db.session.rollback()
    assert db.session.get(StorageMove, move["id"]).status == "planned"
    assert (
        db.session.get(StoragePlacement, stock["units"][2]["id"]).shelf_id
        == stock["shelves"][0]["id"]
    )


def test_batch_cannot_claim_same_stack_position_twice(stock):
    type_id = stock["type"]["id"]
    save_stack_rule(
        {
            "lower_type_id": type_id,
            "upper_type_id": type_id,
            "verified": True,
            "height_increment_mm": 40,
        }
    )
    target = stock["units"][0]["id"]
    move = create_move(
        {
            "kind": "unit",
            "idempotency_key": "overlap-support",
            "items": [
                {
                    "unit_id": stock["units"][1]["id"],
                    "target_placement": {"support_unit_id": target},
                },
                {
                    "unit_id": stock["units"][2]["id"],
                    "target_placement": {"support_unit_id": target},
                },
            ],
        }
    )
    with pytest.raises(Conflict):
        plan_move(move["id"])
    db.session.rollback()
    assert (
        db.session.get(StoragePlacement, stock["units"][1]["id"]).support_unit_id
        is None
    )
    assert (
        db.session.get(StoragePlacement, stock["units"][2]["id"]).support_unit_id
        is None
    )


def test_part_search_distinguishes_current_and_planned_destination(stock, client):
    from services.storage_service import list_part_locations

    source = db.session.get(PartStorage, stock["source"])
    before = list_part_locations("p", 1)
    current = next(row for row in before if row["id"] == source.id)
    assert current["planned_moves"] == []
    move = create_move(
        {
            "kind": "quantity",
            "storage_id": source.id,
            "target_unit_id": stock["units"][1]["id"],
            "quantity": 4,
            "idempotency_key": "search-planned",
            "reason": "Test search",
        }
    )
    plan_move(move["id"])
    response = client.get("/warehouse/parts/p/locations?color_id=1")
    assert response.status_code == 200
    planned = next(
        row for row in response.get_json()["items"] if row["id"] == source.id
    )
    assert planned["quantity"] == 10
    assert planned["address"]["display"] == current["address"]["display"]
    assert planned["address"]["shelf_id"] == current["address"]["shelf_id"]
    assert [
        (loc["id"], loc["label"]) for loc in planned["address"]["location_path"]
    ] == [(loc["id"], loc["label"]) for loc in current["address"]["location_path"]]
    assert planned["planned_moves"][0]["id"] == move["id"]
    assert planned["planned_moves"][0]["quantity"] == 4
    assert "6" in planned["planned_moves"][0]["destination"]
    confirm_move(move["id"])
    after = next(row for row in list_part_locations("p", 1) if row["id"] == source.id)
    assert after["quantity"] == 6
    assert after["planned_moves"] == []
