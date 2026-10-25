"""Behavioral contracts for manual-entry and box-maintenance routes."""

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from models import PartStorage, RebrickablePartCategories, RebrickableParts, db


@pytest.fixture
def stored_part(app):
    """Create one catalog part and one storage record for route tests."""
    with app.app_context():
        category = RebrickablePartCategories(id=1, name="Bricks")
        part = RebrickableParts(
            part_num="3001",
            name="Brick 2 x 4",
            part_cat_id=category.id,
            part_img_url="https://example.test/3001.png",
        )
        storage = PartStorage(
            part_num=part.part_num,
            location="A",
            level="1",
            box="2",
            notes="test part",
        )
        db.session.add_all([category, part, storage])
        db.session.commit()
        return storage.id


class TestBoxMaintenanceContracts:
    def test_page_exposes_avery_label_queue(self, client):
        response = client.get("/box_maintenance")
        script = Path("brick_manager/static/js/box_maintenance_new.js").read_text()

        assert response.status_code == 200
        assert b"Avery 3474 Label Queue" in response.data
        assert b'id="label-start-position"' in response.data
        assert b'id="confirm-label-sheet"' in response.data
        assert b"Select next filtered sheet" in response.data
        assert b'id="clear-label-selection"' in response.data
        assert b'id="label-location-filter"' in response.data
        assert b'id="label-level-filter"' in response.data
        assert b'id="label-box-filter"' in response.data
        assert b'id="label-status-filter"' in response.data
        assert b'id="label-horizontal-offset"' in response.data
        assert b'id="label-vertical-offset"' in response.data
        assert "let available = 25 - firstSlot;" in script
        assert "box[field].trim() !== ''" in script
        assert "function applyFilters()" in script
        assert "checkbox.checked = false;" in script
        assert "avery_3474_box_labels_x${payload.horizontal_offset_mm}" in script

    def test_filter_endpoints_return_distinct_location_hierarchy(
        self, client, stored_part
    ):
        assert client.get("/box_maintenance/filter_data").get_json() == {
            "locations": ["A"]
        }
        assert client.get("/box_maintenance/filter_data?location=A").get_json() == {
            "levels": ["1"]
        }
        assert client.get(
            "/box_maintenance/filter_data?location=A&level=1"
        ).get_json() == {"boxes": ["2"]}

    def test_box_contents_reports_catalog_and_storage_data(self, client, stored_part):
        response = client.get("/box_maintenance/contents?location=A&level=1&box=2")

        assert response.status_code == 200
        assert response.get_json() == [
            {
                "part_num": "3001",
                "img_url": "https://example.test/3001.png",
                "category": "Bricks",
                "name": "Brick 2 x 4",
                "storage_id": stored_part,
            }
        ]

    def test_box_contents_requires_complete_location(self, client):
        response = client.get("/box_maintenance/contents?location=A")

        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid request."}

    def test_update_label_status_persists_boolean_value(self, app, client, stored_part):
        response = client.post(
            "/box_maintenance/update_label_status",
            json={"storage_id": stored_part, "label_printed": True},
        )

        assert response.status_code == 200
        with app.app_context():
            assert db.session.get(PartStorage, stored_part).label_printed is True

    def test_update_label_status_rejects_unknown_storage(self, client):
        response = client.post(
            "/box_maintenance/update_label_status",
            json={"storage_id": 999, "label_printed": True},
        )

        assert response.status_code == 404
        assert response.get_json() == {"error": "Part storage entry not found."}

    def test_update_part_location_persists_all_location_fields(
        self, app, client, stored_part
    ):
        with app.app_context():
            db.session.get(PartStorage, stored_part).label_printed = True
            companion = PartStorage(
                part_num="3001",
                location="A",
                level="1",
                box="2",
                label_printed=True,
            )
            db.session.add(companion)
            db.session.commit()
            companion_id = companion.id
        response = client.post(
            "/box_maintenance/update_part_location",
            json={"storage_id": stored_part, "location": "B", "level": "3", "box": "4"},
        )

        assert response.status_code == 200
        with app.app_context():
            storage = db.session.get(PartStorage, stored_part)
            assert (storage.location, storage.level, storage.box) == ("B", "3", "4")
            assert storage.label_printed is False
            assert db.session.get(PartStorage, companion_id).label_printed is False

    def test_label_queue_groups_storage_rows_by_box(self, client, stored_part):
        db.session.add_all(
            [
                PartStorage(part_num="3001", location="", level="", box=""),
                PartStorage(part_num="3001", location="  ", level="1", box="9"),
            ]
        )
        db.session.commit()

        response = client.get("/box_maintenance/label_queue")

        assert response.status_code == 200
        assert response.get_json() == {
            "boxes": [
                {
                    "location": "A",
                    "level": "1",
                    "box": "2",
                    "part_count": 1,
                    "label_printed": False,
                }
            ],
            "sheet_capacity": 24,
        }

    def test_label_sheet_generates_avery_pdf_for_selected_box(
        self, client, stored_part
    ):
        with patch(
            "routes.box_maintenance.create_avery_3474_pdf",
            return_value=BytesIO(b"%PDF-test"),
        ) as create_pdf:
            response = client.post(
                "/box_maintenance/label_sheet",
                json={
                    "boxes": [{"location": "A", "level": "1", "box": "2"}],
                    "start_position": 4,
                },
            )

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert response.data == b"%PDF-test"
        assert (
            "avery_3474_box_labels_x0_y0.pdf" in response.headers["Content-Disposition"]
        )
        box_info = create_pdf.call_args.args[0][0]
        assert box_info["box"] == "2"
        assert box_info["items"][0]["part_num"] == "3001"
        assert create_pdf.call_args.kwargs == {
            "start_position": 4,
            "horizontal_offset_mm": 0,
            "vertical_offset_mm": 0,
        }

    def test_confirm_print_marks_every_row_in_box_printed(
        self, app, client, stored_part
    ):
        response = client.post(
            "/box_maintenance/label_sheet/printed",
            json={"boxes": [{"location": "A", "level": "1", "box": "2"}]},
        )

        assert response.status_code == 200
        assert response.get_json()["updated"] == 1
        with app.app_context():
            assert db.session.get(PartStorage, stored_part).label_printed is True

    @pytest.mark.parametrize(
        "payload",
        [None, {}, {"boxes": []}, {"boxes": [{}]}, {"boxes": "A-1-2"}],
    )
    def test_label_sheet_rejects_invalid_box_selection(self, client, payload):
        response = client.post("/box_maintenance/label_sheet", json=payload)

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "field,value",
        [
            ("horizontal_offset_mm", 10.1),
            ("vertical_offset_mm", -10.1),
            ("horizontal_offset_mm", "1"),
            ("vertical_offset_mm", True),
        ],
    )
    def test_label_sheet_rejects_invalid_print_offsets(
        self, client, stored_part, field, value
    ):
        payload = {
            "boxes": [{"location": "A", "level": "1", "box": "2"}],
            field: value,
        }

        response = client.post("/box_maintenance/label_sheet", json=payload)

        assert response.status_code == 400

    def test_delete_part_storage_removes_the_record(self, app, client, stored_part):
        with app.app_context():
            companion = PartStorage(
                part_num="3001",
                location="A",
                level="1",
                box="2",
                label_printed=True,
            )
            db.session.add(companion)
            db.session.commit()
            companion_id = companion.id
        response = client.delete(f"/box_maintenance/delete_part/{stored_part}")

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "Part 3001 removed from storage successfully."
        }
        with app.app_context():
            assert db.session.get(PartStorage, stored_part) is None
            assert db.session.get(PartStorage, companion_id).label_printed is False

    def test_location_overview_groups_parts_by_box(self, client, stored_part):
        with patch(
            "routes.box_maintenance.cache_image", return_value="/cached/3001.png"
        ):
            response = client.get("/box_maintenance/location_overview/A")

        assert response.status_code == 200
        assert response.get_json() == [
            {
                "location": "A",
                "level": "1",
                "box": "2",
                "part_count": 1,
                "img_url": "/cached/3001.png",
            }
        ]


class TestManualEntryContracts:
    def test_validate_part_returns_storage_locations(self, client, stored_part):
        with patch("routes.manual_entry.cache_image", return_value="/cached/3001.png"):
            response = client.get("/manual_entry/validate_part/3001")

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["exists"] is True
        assert payload["has_storage"] is True
        assert payload["storage_count"] == 1
        assert payload["storage_info"]["location"] == "A"
        assert payload["part_info"] == {
            "name": "Brick 2 x 4",
            "category": "Bricks",
            "image_url": "/cached/3001.png",
        }

    def test_validate_part_returns_404_for_unknown_catalog_part(self, client):
        response = client.get("/manual_entry/validate_part/not-found")

        assert response.status_code == 404
        assert response.get_json() == {
            "exists": False,
            "message": "Part not found in Rebrickable database",
        }

    def test_delete_storage_removes_the_requested_location(
        self, app, client, stored_part
    ):
        response = client.delete(f"/manual_entry/delete_storage/{stored_part}")

        assert response.status_code == 200
        with app.app_context():
            assert db.session.get(PartStorage, stored_part) is None

    def test_delete_storage_reports_missing_location(self, client):
        response = client.delete("/manual_entry/delete_storage/999")

        assert response.status_code == 404
        assert response.get_json() == {"error": "Storage location not found"}


class TestLegacyStoragePageContracts:
    def test_storage_form_renders_requested_part(self, client):
        response = client.get("/add_to_storage/3001")

        assert response.status_code == 200
        assert b"3001" in response.data

    def test_storage_form_updates_lookup_and_application_cache(self, app, client):
        with (
            patch("routes.storage.load_part_lookup", return_value={}) as load,
            patch("routes.storage.save_part_lookup") as save,
        ):
            response = client.post(
                "/add_to_storage/3001",
                data={"location": "A", "level": "2", "box": "7"},
            )

        assert response.status_code == 302
        load.assert_called_once_with()
        expected = {"3001": {"location": "A", "level": "2", "box": "7"}}
        save.assert_called_once_with(expected)
        assert app.config["MASTER_LOOKUP"] == expected
