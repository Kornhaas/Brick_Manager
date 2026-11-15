"""Old entrypoints cannot bypass confirmed physical storage or API authentication."""

import pytest
from models import (
    PartStorage,
    RebrickablePartCategories,
    RebrickableParts,
    StorageUnit,
    db,
)
from services.part_lookup_service import invalidate_part_lookup_cache, load_part_lookup


@pytest.fixture
def structured(app):
    db.session.add(RebrickablePartCategories(id=991, name="Test Bricks"))
    db.session.add(
        RebrickableParts(part_num="legacy-test", name="Bricks", part_cat_id=991)
    )
    unit = StorageUnit(label="6", kind="container", contents_complete=True)
    db.session.add(unit)
    db.session.flush()
    entry = PartStorage(
        part_num="legacy-test",
        storage_unit_id=unit.id,
        quantity=10,
        location="old",
        level="2",
        box="6",
    )
    db.session.add(entry)
    db.session.commit()
    invalidate_part_lookup_cache()
    return entry.id


@pytest.mark.parametrize(
    "path",
    [
        "/update_part_location",
        "/upload/save_storage_location",
        "/save_locations",
        "/add_to_storage/legacy-test",
    ],
)
def test_old_part_writers_cannot_change_physical_place(client, structured, path):
    body = {"part_num": "legacy-test", "location": "wrong", "level": "4", "box": "3"}
    if path == "/save_locations":
        body = {"legacy-test": body}
    response = client.post(path, json=body)
    assert response.status_code == 409
    assert db.session.get(PartStorage, structured).location == "old"
    assert db.session.get(PartStorage, structured).quantity == 10


@pytest.mark.parametrize(
    "path", ["/box_maintenance/delete_part/{id}", "/manual_entry/delete_storage/{id}"]
)
def test_old_delete_preserves_counted_inventory(client, structured, path):
    response = client.delete(path.format(id=structured))
    assert response.status_code == 409
    assert db.session.get(PartStorage, structured).quantity == 10


def test_desktop_checks_credentials_before_storage_conflict(client, structured):
    path = "/api/v1/parts/legacy-test/storage"
    payload = {"location": "wrong", "level": "4", "box": "3"}
    assert client.put(path, json=payload).status_code == 401
    response = client.put(
        path, json=payload, headers={"Authorization": "Bearer test-client-api-key"}
    )
    assert response.status_code == 409
    assert db.session.get(PartStorage, structured).location == "old"


def test_lookup_keeps_all_locations_and_stable_deeplinks(client, structured):
    db.session.add(
        PartStorage(part_num="legacy-test", location="Other", level="9", box="6")
    )
    db.session.commit()
    invalidate_part_lookup_cache()
    lookup = load_part_lookup()["legacy-test"]
    assert lookup["location"] is None
    assert len(lookup["locations"]) == 2
    response = client.post("/lookup_part", data={"part_id": "legacy-test"})
    assert response.status_code == 200
    assert b"/warehouse?unit_id=" in response.data
    assert b"Other" in response.data
    invalidate_part_lookup_cache()
