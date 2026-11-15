"""Explicit reprints survive reloads and never confuse download with printing."""

import pytest
from models import ConfigSettings, PartStorage, RebrickableInventoryParts, db
from services.storage_service import create_type, create_unit

from brick_manager.tests.test_warehouse_legacy_overview import (
    legacy_shelf as _legacy_shelf,
)


@pytest.fixture
def legacy_shelf(app):
    return _legacy_shelf.__wrapped__(app)


def mark(client, storage_id):
    response = client.post(
        "/warehouse/label-marks", json={"storage_id": storage_id, "marked": True}
    )
    assert response.status_code == 200
    return client.get("/warehouse/label-marks").get_json()["marks"]


def test_explicit_reprints_survive_reload_and_preserve_existing_print_status(
    client, legacy_shelf
):
    rows = PartStorage.query.filter_by(box="6").all()
    for row in rows:
        row.label_printed = True
    db.session.commit()
    entries = mark(client, rows[0].id)
    assert len(entries) == 1
    assert entries[0]["target"] == {"location": "01", "level": "4", "box": "6"}
    assert all(row.label_printed for row in rows)
    assert client.get("/warehouse/label-marks").get_json()["marks"] == entries
    assert (
        client.post(
            "/warehouse/label-marks", json={"storage_id": rows[1].id, "marked": True}
        ).status_code
        == 200
    )
    assert len(client.get("/warehouse/label-marks").get_json()["marks"]) == 1
    assert (
        client.post(
            "/warehouse/label-marks", json={"storage_id": rows[0].id, "marked": False}
        ).status_code
        == 200
    )
    assert client.get("/warehouse/label-marks").get_json()["marks"] == []
    assert all(row.label_printed for row in rows)


def test_pdf_download_preserves_marks_until_confirmed(
    client, legacy_shelf, monkeypatch
):
    from io import BytesIO

    import routes.warehouse as route

    calls = []

    def render(infos, *args):
        calls.append(infos)
        return BytesIO(b"%PDF-test")

    monkeypatch.setattr(route, "create_avery_3474_pdf", render)
    row = PartStorage.query.filter_by(box="6").first()
    entries = mark(client, row.id)
    response = client.post("/warehouse/label-marks/sheet", json={"marks": entries})
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert calls[0][0]["box"] == "6"
    assert len(client.get("/warehouse/label-marks").get_json()["marks"]) == 1
    assert not db.session.get(PartStorage, row.id).label_printed
    assert (
        client.post(
            "/warehouse/label-marks/printed", json={"marks": entries}
        ).status_code
        == 200
    )
    assert client.get("/warehouse/label-marks").get_json()["marks"] == []
    assert all(row.label_printed for row in PartStorage.query.filter_by(box="6").all())
    assert not PartStorage.query.filter_by(box="9").first().label_printed
    assert (
        client.post(
            "/warehouse/label-marks/printed", json={"marks": entries}
        ).status_code
        == 409
    )


def test_stale_or_remarked_box_cannot_be_confirmed(client, legacy_shelf):
    row = PartStorage.query.filter_by(box="6").first()
    old = mark(client, row.id)
    new = mark(client, row.id)
    assert old[0]["generation"] != new[0]["generation"]
    assert (
        client.post("/warehouse/label-marks/printed", json={"marks": old}).status_code
        == 409
    )
    row.box = "99"
    db.session.commit()
    assert (
        client.post("/warehouse/label-marks/printed", json={"marks": new}).status_code
        == 409
    )
    assert len(client.get("/warehouse/label-marks").get_json()["marks"]) == 1


def test_unit_reprints_have_stable_identity(client, legacy_shelf):
    kind = create_type({"name": "Label unit", "kind": "container"})
    a = create_unit({"type_id": kind["id"], "label": "6"})
    b = create_unit({"type_id": kind["id"], "label": "6"})
    for unit in [a, b]:
        assert (
            client.post(
                "/warehouse/label-marks", json={"unit_id": unit["id"], "marked": True}
            ).status_code
            == 200
        )
    entries = client.get("/warehouse/label-marks").get_json()["marks"]
    assert len(entries) == 2
    assert (
        client.post(
            "/warehouse/label-marks/printed", json={"marks": [entries[0]]}
        ).status_code
        == 200
    )
    assert len(client.get("/warehouse/label-marks").get_json()["marks"]) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"marked": "yes", "storage_id": 1},
        {"marked": True, "storage_id": True},
        {"marked": True, "unit_id": 999999},
        {"marked": True},
    ],
)
def test_invalid_queue_requests_are_rejected(client, payload):
    assert client.post("/warehouse/label-marks", json=payload).status_code in {400, 404}
    assert (
        ConfigSettings.query.filter(
            ConfigSettings.key.startswith("warehouse_label_request:")
        ).count()
        == 0
    )


def test_incomplete_address_and_missing_csrf_rejected(
    app, client, legacy_shelf, monkeypatch
):
    row = PartStorage.query.filter_by(box="?").first()
    assert (
        client.post(
            "/warehouse/label-marks", json={"storage_id": row.id, "marked": True}
        ).status_code
        == 400
    )
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    assert (
        client.post(
            "/warehouse/label-marks", json={"storage_id": row.id, "marked": True}
        ).status_code
        == 403
    )


def test_inventory_images_fill_missing_master_images(client, legacy_shelf):
    from models import (
        RebrickableColors,
        RebrickableInventories,
        RebrickableSets,
        RebrickableThemes,
    )

    db.session.add(
        RebrickableColors(id=991, name="Image color", rgb="FFFFFF", is_trans=False)
    )
    db.session.add(RebrickableThemes(id=991, name="Image theme"))
    db.session.flush()
    db.session.add(
        RebrickableSets(
            set_num="img-set", name="Image set", year=2000, num_parts=1, theme_id=991
        )
    )
    db.session.flush()
    db.session.add(RebrickableInventories(id=991, version=1, set_num="img-set"))
    db.session.flush()
    db.session.add(
        RebrickableInventoryParts(
            inventory_id=991,
            part_num="legacy-shelf-part",
            color_id=991,
            quantity=1,
            is_spare=False,
            img_url="https://example.test/inventory.png",
        )
    )
    from models import RebrickableParts

    db.session.get(RebrickableParts, "legacy-shelf-part").part_img_url = None
    db.session.commit()
    data = client.get("/warehouse/data").get_json()
    assert all(
        row["part_img_url"] == "https://example.test/inventory.png"
        for row in data["contents"]
    )


def test_stale_mark_can_be_removed_without_affecting_other_settings(
    client, legacy_shelf
):
    row = PartStorage.query.filter_by(box="6").first()
    entry = mark(client, row.id)[0]
    row.location = None
    db.session.commit()
    assert client.post("/warehouse/label-marks/remove", json=entry).status_code == 200
    assert client.get("/warehouse/label-marks").get_json()["marks"] == []
    assert (
        client.post(
            "/warehouse/label-marks/remove", json={"key": "unrelated_setting"}
        ).status_code
        == 400
    )


@pytest.mark.parametrize(
    "data",
    [
        {"marks": []},
        {"marks": [True]},
        {"marks": [], "start_position": True},
        {"marks": [], "horizontal_offset_mm": float("inf")},
    ],
)
def test_malformed_batches_do_not_change_marks(client, legacy_shelf, data):
    row = PartStorage.query.filter_by(box="6").first()
    mark(client, row.id)
    assert client.post("/warehouse/label-marks/sheet", json=data).status_code == 400
    assert len(client.get("/warehouse/label-marks").get_json()["marks"]) == 1
