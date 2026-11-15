"""Existing address assignments remain visible without inventing physical boxes."""

import pytest
from models import (
    PartStorage,
    RebrickablePartCategories,
    RebrickableParts,
    StorageUnit,
    db,
)
from services.storage_service import create_location, create_type, create_unit


@pytest.fixture
def legacy_shelf(app):
    zone = create_location({"kind": "zone", "label": "Aktiv"})
    rack = create_location({"kind": "rack", "label": "01", "parent_id": zone["id"]})
    shelf = create_location(
        {
            "kind": "shelf",
            "label": "4",
            "parent_id": rack["id"],
            "width_mm": 500,
            "depth_mm": 300,
            "height_profile": [[0, 300], [500, 300]],
            "measurement_status": "measured",
        }
    )
    db.session.add(RebrickablePartCategories(id=941, name="Bricks"))
    db.session.add(
        RebrickableParts(
            part_num="legacy-shelf-part",
            name="Existing Bricks",
            part_cat_id=941,
            part_img_url="https://example.test/brick.png",
        )
    )
    db.session.add_all(
        [
            PartStorage(
                part_num="legacy-shelf-part",
                location="01",
                level="4",
                box="6",
                notes="first record",
            ),
            PartStorage(
                part_num="legacy-shelf-part",
                location="01",
                level="4",
                box="6",
                notes="could be a second physical box",
            ),
            PartStorage(
                part_num="legacy-shelf-part", location="01", level="4", box="9"
            ),
            PartStorage(
                part_num="legacy-shelf-part", location=None, level=None, box="?"
            ),
        ]
    )
    db.session.commit()
    return shelf


def test_existing_boxes_project_into_overview_without_new_physical_units(
    client, legacy_shelf
):
    response = client.get("/warehouse/data")
    assert response.status_code == 200
    data = response.get_json()
    groups = [
        group
        for group in data["legacy_groups"]
        if group["shelf_id"] == legacy_shelf["id"]
    ]
    assert {group["box"] for group in groups} == {"6", "9"}
    six = next(group for group in groups if group["box"] == "6")
    assert six["row_count"] == 2
    assert six["physical_verified"] is False
    assert six["variant_count"] == 1
    assert all(row["quantity"] is None for row in six["contents"])
    assert six["contents"][0]["part_name"] == "Existing Bricks"
    assert six["contents"][0]["part_img_url"] == "https://example.test/brick.png"
    assert {row["notes"] for row in six["contents"]} == {
        "first record",
        "could be a second physical box",
    }
    assert data["legacy_summary"]["legacy_rows"] == 4
    assert data["legacy_summary"]["unlocated_legacy_rows"] == 1
    assert StorageUnit.query.count() == 0
    assert PartStorage.query.count() == 4


def test_legacy_occupancy_prevents_falsely_free_measured_shelf(client, legacy_shelf):
    data = client.get(f"/warehouse/locations/{legacy_shelf['id']}").get_json()
    assert data["fit_known"] is False
    assert data["free_intervals_mm"] == []
    assert data["legacy_rows"] == 3


def test_duplicate_shelf_labels_remain_unassigned_in_projection(client, legacy_shelf):
    original = client.get("/warehouse/data").get_json()
    shelf = next(
        loc for loc in original["locations"] if loc["id"] == legacy_shelf["id"]
    )
    create_location({"kind": "shelf", "label": "4", "parent_id": shelf["parent_id"]})
    groups = client.get("/warehouse/data").get_json()["legacy_groups"]
    six = next(group for group in groups if group["box"] == "6")
    assert six["shelf_id"] is None
    assert len(six["shelf_candidates"]) == 2
    assert six["row_count"] == 2
    assert StorageUnit.query.count() == 0


def test_confirming_legacy_row_removes_only_that_row_from_preview(client, legacy_shelf):
    row = PartStorage.query.filter_by(box="6").order_by(PartStorage.id).first()
    row_id = row.id
    kind = create_type({"name": "Observed container"})
    unit = create_unit({"type_id": kind["id"], "label": "6"})
    response = client.patch(
        f"/warehouse/contents/{row_id}",
        json={"storage_unit_id": unit["id"], "revision": row.revision},
    )
    assert response.status_code == 200
    data = client.get("/warehouse/data").get_json()
    assert data["legacy_summary"]["legacy_rows"] == 3
    assert all(row_id not in group["storage_ids"] for group in data["legacy_groups"])
    assert (
        next(group for group in data["legacy_groups"] if group["box"] == "6")[
            "row_count"
        ]
        == 1
    )
    assert PartStorage.query.count() == 4


def test_unmapped_legacy_data_never_produces_positive_fit_claim(client, legacy_shelf):
    kind = create_type(
        {
            "name": "Measured empty box",
            "width_mm": 100,
            "depth_mm": 100,
            "height_mm": 50,
            "dimensions_status": "measured",
        }
    )
    unit = create_unit({"type_id": kind["id"], "label": "New"})
    response = client.post(
        f"/warehouse/units/{unit['id']}/preview",
        json={"shelf_id": legacy_shelf["id"], "x_mm": 0, "depth_offset_mm": 0},
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "unknown"
    assert response.get_json()["legacy_rows"] == 3


def test_focused_overview_omits_unresolved_contents_and_keeps_global_counts(
    client, legacy_shelf
):
    data = client.get("/warehouse/data?view=focused").get_json()
    assert data["selected_shelf_id"] == legacy_shelf["id"]
    assert len(data["contents"]) == 3
    assert data["legacy_summary"]["content_rows"] == 4
    unknown = [group for group in data["legacy_groups"] if group["shelf_id"] is None]
    assert len(unknown) == 1 and "contents" not in unknown[0]
    group = client.get(
        f"/warehouse/contents/{unknown[0]['storage_ids'][0]}/group"
    ).get_json()
    assert len(group["contents"]) == 1
    assert group["contents"][0]["part_name"] == "Existing Bricks"


def test_empty_selected_shelf_does_not_load_other_shelf_contents(
    client, legacy_shelf, monkeypatch
):
    from models import StorageLocation
    from services import storage_service

    original = db.session.get(StorageLocation, legacy_shelf["id"])
    shelf = create_location(
        {"kind": "shelf", "label": "10", "parent_id": original.parent_id}
    )
    queried = []
    monkeypatch.setattr(
        storage_service,
        "catalog_images",
        lambda part_nums: queried.append(part_nums) or {},
    )
    data = client.get(f"/warehouse/data?view=focused&shelf_id={shelf['id']}").get_json()
    assert data["selected_shelf_id"] == shelf["id"]
    assert data["contents"] == []
    assert all(group["shelf_id"] is None for group in data["legacy_groups"])
    assert queried == [set()]
    assert data["legacy_summary"]["legacy_rows"] == 4


def test_focused_all_and_stale_shelf_fallback(client, legacy_shelf):
    data = client.get("/warehouse/data?view=focused&shelf_id=999999").get_json()
    assert data["selected_shelf_id"] == legacy_shelf["id"]
    assert len(data["contents"]) == 3
    assert (
        len(client.get("/warehouse/data?view=focused&all=1").get_json()["contents"])
        == 4
    )
    assert len(client.get("/warehouse/contents").get_json()["items"]) == 4
