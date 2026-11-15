"""Physical structure and geometry contracts exercised through storage services."""

import pytest
from models import (
    PartStorage,
    RebrickablePartCategories,
    RebrickableParts,
    StorageUnit,
    db,
)
from services.storage_service import (
    create_location,
    create_type,
    create_unit,
    partition_drawer,
    place_unit,
    preview_placement,
    save_content,
    save_stack_rule,
    seed_container_types,
    space_report,
    unit_address,
    unit_details,
    update_content,
)
from werkzeug.exceptions import BadRequest, Conflict


@pytest.fixture
def structure(app):
    zone = create_location({"kind": "zone", "label": "Testbereich"})
    rack = create_location(
        {"kind": "rack", "label": "Testregal", "parent_id": zone["id"]}
    )
    shelf = create_location(
        {
            "kind": "shelf",
            "label": "Testfach",
            "parent_id": rack["id"],
            "width_mm": 500,
            "depth_mm": 300,
            "height_profile": [[0, 1500], [500, 1500]],
            "measurement_status": "measured",
        }
    )
    ctype = create_type(
        {
            "name": "Gemessene Testbox",
            "width_mm": 100,
            "depth_mm": 100,
            "height_mm": 50,
            "dimensions_status": "measured",
            "access_mode": "remove_above",
        }
    )
    db.session.add(RebrickablePartCategories(id=1, name="Bricks"))
    db.session.add(RebrickableParts(part_num="p", name="Part", part_cat_id=1))
    db.session.commit()
    return {"zone": zone, "rack": rack, "shelf": shelf, "type": ctype}


def test_duplicate_labels_do_not_create_duplicate_identity(structure):
    a = create_unit({"label": "6", "type_id": structure["type"]["id"]})
    b = create_unit({"label": "6", "type_id": structure["type"]["id"]})
    assert a["id"] != b["id"]
    assert a["label"] == b["label"] == "6"
    place_unit(
        a["id"], {"shelf_id": structure["shelf"]["id"], "x_mm": 0, "depth_offset_mm": 0}
    )
    place_unit(
        b["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 100, "depth_offset_mm": 0},
    )
    assert unit_address(a["id"])["shelf_id"] == structure["shelf"]["id"]
    assert unit_address(b["id"])["unit_path"][-1]["id"] == b["id"]
    with pytest.raises(Conflict, match="bestätigte Bewegung"):
        place_unit(a["id"], {"shelf_id": structure["shelf"]["id"]})


def test_hmh_stacks_same_size_only_and_front_access_stays_open(structure):
    types = {row["name"]: row for row in seed_container_types()}
    assert len(seed_container_types()) == len(types) == 10
    assert "HMH XS" in types and "STANLEY 1-93-980" in types
    lower = create_unit({"label": "3", "type_id": types["HMH S"]["id"]})
    same = create_unit({"label": "4", "type_id": types["HMH S"]["id"]})
    other = create_unit({"label": "5", "type_id": types["HMH XS"]["id"]})
    place_unit(lower["id"], {"shelf_id": structure["shelf"]["id"]})
    save_stack_rule(
        {
            "lower_type_id": types["HMH S"]["id"],
            "upper_type_id": types["HMH S"]["id"],
            "verified": True,
            "height_increment_mm": 50,
        }
    )
    place_unit(same["id"], {"support_unit_id": lower["id"], "relation_kind": "stacked"})
    assert unit_details(lower["id"])["access_requires_removal"] == []
    with pytest.raises(Conflict, match="derselben Größe"):
        place_unit(
            other["id"], {"support_unit_id": lower["id"], "observed_unverified": True}
        )
    with pytest.raises(Conflict, match="unterschiedlicher Größe"):
        save_stack_rule(
            {
                "lower_type_id": types["HMH S"]["id"],
                "upper_type_id": types["HMH XS"]["id"],
                "verified": True,
            }
        )


def test_loose_support_is_distinct_from_interlocking_stack(structure):
    types = {row["name"]: row for row in seed_container_types()}
    lower = create_unit({"label": "9", "type_id": types["CYEER 750 ml"]["id"]})
    upper = create_unit({"label": "Becher", "type_id": types["Feinkost 125 ml"]["id"]})
    place_unit(lower["id"], {"shelf_id": structure["shelf"]["id"]})
    with pytest.raises(Conflict, match="nicht verifiziert"):
        place_unit(
            upper["id"], {"support_unit_id": lower["id"], "relation_kind": "loose_on"}
        )
    save_stack_rule(
        {
            "lower_type_id": lower["type_id"],
            "upper_type_id": upper["type_id"],
            "relation_kind": "loose_on",
            "verified": True,
        }
    )
    result = place_unit(
        upper["id"], {"support_unit_id": lower["id"], "relation_kind": "loose_on"}
    )
    assert result["placement"]["relation_kind"] == "loose_on"
    assert unit_details(lower["id"])["access_requires_removal"] == [upper["id"]]
    assert (
        preview_placement(
            upper["id"], {"support_unit_id": lower["id"], "relation_kind": "loose_on"}
        )["status"]
        == "unknown"
    )


def test_twenty_level_stack_resolves_every_level_and_rejects_cycle(structure):
    ctype = structure["type"]["id"]
    save_stack_rule(
        {
            "lower_type_id": ctype,
            "upper_type_id": ctype,
            "verified": True,
            "height_increment_mm": 50,
        }
    )
    units = [create_unit({"label": str(i + 1), "type_id": ctype}) for i in range(20)]
    place_unit(
        units[0]["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 0, "depth_offset_mm": 0},
    )
    for below, above in zip(units, units[1:], strict=False):
        place_unit(above["id"], {"support_unit_id": below["id"], "depth_offset_mm": 0})
    address = unit_address(units[-1]["id"])
    assert len(address["unit_path"]) == 20
    assert address["shelf_id"] == structure["shelf"]["id"]
    with pytest.raises(Conflict, match="Zyklus"):
        preview_placement(units[0]["id"], {"support_unit_id": units[-1]["id"]})


@pytest.mark.parametrize(
    "name,count", [("STANLEY 1-93-980", 30), ("STANLEY 1-93-978", 9)]
)
def test_magazine_drawers_and_partitions_have_stable_addresses(structure, name, count):
    types = {row["name"]: row for row in seed_container_types()}
    cabinet = create_unit({"label": "Magazin", "type_id": types[name]["id"]})
    assert len(cabinet["children"]) == count
    place_unit(cabinet["id"], {"shelf_id": structure["shelf"]["id"]})
    drawer = cabinet["children"][0]
    partitioned = partition_drawer(drawer["id"], {"partition_count": 2})
    children = partitioned["children"]
    assert [child["label"] for child in children] == ["A", "B"]
    repeat = partition_drawer(drawer["id"], {"partition_count": 2})
    assert [c["id"] for c in repeat["children"]] == [c["id"] for c in children]
    entry = save_content({"storage_unit_id": children[0]["id"], "part_num": "p"})
    assert unit_address(children[0]["id"])["unit_path"][-3:] == [
        {"id": cabinet["id"], "label": "Magazin", "kind": "cabinet"},
        {"id": drawer["id"], "label": "1", "kind": "drawer"},
        {"id": children[0]["id"], "label": "A", "kind": "compartment"},
    ]
    with pytest.raises(Conflict, match="Inhalt zuerst"):
        partition_drawer(drawer["id"], {"partition_count": 3})
    db.session.rollback()
    assert db.session.get(PartStorage, entry["id"]).storage_unit_id == children[0]["id"]
    with pytest.raises(BadRequest, match="adressierbare Unterteilung"):
        save_content({"storage_unit_id": drawer["id"], "part_num": "p"})
    assert db.session.get(StorageUnit, children[0]["id"]).active is True


def test_sloping_roof_checked_over_full_width_and_missing_data_remain_unknown(
    structure,
):
    rack = structure["rack"]["id"]
    slope = create_location(
        {
            "kind": "shelf",
            "label": "Schräge",
            "parent_id": rack,
            "width_mm": 200,
            "depth_mm": 100,
            "height_profile": [[0, 100], [200, 20]],
            "measurement_status": "measured",
        }
    )
    unit = create_unit({"label": "Randkollision", "type_id": structure["type"]["id"]})
    result = preview_placement(
        unit["id"], {"shelf_id": slope["id"], "x_mm": 100, "depth_offset_mm": 0}
    )
    assert result["status"] == "no_fit"
    assert any("Dachschräge" in reason for reason in result["reasons"])
    unknown = preview_placement(unit["id"], {"shelf_id": structure["shelf"]["id"]})
    assert unknown["status"] == "unknown"
    assert unknown["reasons"]


def test_empty_containers_still_occupy_ground_area_and_gaps_stay_separate(structure):
    for x, label in [(100, "2"), (300, "5")]:
        unit = create_unit(
            {
                "label": label,
                "type_id": structure["type"]["id"],
                "contents_complete": True,
            }
        )
        assert unit["empty"] is True
        place_unit(
            unit["id"],
            {"shelf_id": structure["shelf"]["id"], "x_mm": x, "depth_offset_mm": 0},
        )
    report = space_report(structure["shelf"]["id"])
    assert report["base_count"] == 2
    assert report["free_intervals_mm"] == [[0, 100], [200, 300], [400, 500]]
    wide = create_type(
        {
            "name": "180 mm",
            "width_mm": 180,
            "depth_mm": 100,
            "height_mm": 50,
            "dimensions_status": "measured",
        }
    )
    unit = create_unit({"label": "6", "type_id": wide["id"]})
    for x in (0, 200):
        assert (
            preview_placement(
                unit["id"],
                {"shelf_id": structure["shelf"]["id"], "x_mm": x, "depth_offset_mm": 0},
            )["status"]
            == "no_fit"
        )


def test_first_count_requires_reason_and_is_audited(structure):
    unit = create_unit({"label": "count", "type_id": structure["type"]["id"]})
    entry = save_content({"storage_unit_id": unit["id"], "part_num": "p"})
    assert entry["quantity"] is None
    with pytest.raises(BadRequest, match="reason"):
        update_content(entry["id"], {"quantity": 10})
    db.session.rollback()
    result = update_content(entry["id"], {"quantity": 10, "reason": "Vor Ort gezählt"})
    assert result["quantity"] == 10
    from models import StorageMove

    count = StorageMove.query.filter_by(kind="count").one()
    assert count.snapshot == {"quantity_before": None, "quantity_after": 10}
    assert count.idempotency_key


def test_unknown_neighbor_position_prevents_a_positive_fit_claim(structure):
    neighbor = create_unit(
        {"label": "Position ungeklärt", "type_id": structure["type"]["id"]}
    )
    place_unit(neighbor["id"], {"shelf_id": structure["shelf"]["id"]})
    candidate = create_unit({"label": "neu", "type_id": structure["type"]["id"]})
    result = preview_placement(
        candidate["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 100, "depth_offset_mm": 0},
    )
    assert result["status"] == "unknown"
    assert result["reasons"]


def test_unknown_neighbor_depth_prevents_known_free_space_claim(structure):
    unknown_depth = create_type(
        {
            "name": "Tiefe unbekannt",
            "width_mm": 100,
            "height_mm": 50,
            "dimensions_status": "measured",
        }
    )
    unit = create_unit({"label": "Tiefe ungeklärt", "type_id": unknown_depth["id"]})
    place_unit(unit["id"], {"shelf_id": structure["shelf"]["id"], "x_mm": 0})
    assert space_report(structure["shelf"]["id"])["fit_known"] is False


def test_supported_stack_height_is_included_when_previewing_base(structure):
    low = create_location(
        {
            "kind": "shelf",
            "label": "Niedrig",
            "parent_id": structure["rack"]["id"],
            "width_mm": 500,
            "depth_mm": 300,
            "height_profile": [[0, 75], [500, 75]],
            "measurement_status": "measured",
        }
    )
    type_id = structure["type"]["id"]
    save_stack_rule(
        {
            "lower_type_id": type_id,
            "upper_type_id": type_id,
            "verified": True,
            "height_increment_mm": 50,
        }
    )
    base = create_unit({"label": "Basis", "type_id": type_id})
    upper = create_unit({"label": "Oben", "type_id": type_id})
    place_unit(
        base["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 0, "depth_offset_mm": 0},
    )
    place_unit(upper["id"], {"support_unit_id": base["id"], "depth_offset_mm": 0})
    result = preview_placement(
        base["id"], {"shelf_id": low["id"], "x_mm": 0, "depth_offset_mm": 0}
    )
    assert result["status"] == "no_fit"


def test_loose_support_rejects_known_offset_outside_support_surface(structure):
    type_id = structure["type"]["id"]
    save_stack_rule(
        {
            "lower_type_id": type_id,
            "upper_type_id": type_id,
            "relation_kind": "loose_on",
            "verified": True,
            "height_increment_mm": 50,
        }
    )
    lower = create_unit({"label": "Unterlage", "type_id": type_id})
    upper = create_unit({"label": "Lose Auflage", "type_id": type_id})
    place_unit(
        lower["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 100, "depth_offset_mm": 0},
    )
    result = preview_placement(
        upper["id"],
        {
            "support_unit_id": lower["id"],
            "relation_kind": "loose_on",
            "x_mm": 250,
            "depth_offset_mm": 0,
        },
    )
    assert result["status"] == "no_fit"


def test_loose_siblings_cannot_overlap_on_same_support_surface(structure):
    type_id = structure["type"]["id"]
    save_stack_rule(
        {
            "lower_type_id": type_id,
            "upper_type_id": type_id,
            "relation_kind": "loose_on",
            "verified": True,
            "height_increment_mm": 50,
        }
    )
    support = create_unit({"label": "Träger", "type_id": type_id})
    first = create_unit({"label": "Erste Auflage", "type_id": type_id})
    second = create_unit({"label": "Zweite Auflage", "type_id": type_id})
    place_unit(
        support["id"],
        {"shelf_id": structure["shelf"]["id"], "x_mm": 0, "depth_offset_mm": 0},
    )
    place_unit(
        first["id"],
        {
            "support_unit_id": support["id"],
            "relation_kind": "loose_on",
            "x_mm": 0,
            "depth_offset_mm": 0,
        },
    )
    assert (
        preview_placement(
            second["id"],
            {
                "support_unit_id": support["id"],
                "relation_kind": "loose_on",
                "x_mm": 0,
                "depth_offset_mm": 0,
            },
        )["status"]
        == "no_fit"
    )
