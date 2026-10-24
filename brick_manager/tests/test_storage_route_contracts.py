"""Behavioral contracts for manual-entry and box-maintenance routes."""

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
        response = client.post(
            "/box_maintenance/update_part_location",
            json={"storage_id": stored_part, "location": "B", "level": "3", "box": "4"},
        )

        assert response.status_code == 200
        with app.app_context():
            storage = db.session.get(PartStorage, stored_part)
            assert (storage.location, storage.level, storage.box) == ("B", "3", "4")

    def test_delete_part_storage_removes_the_record(self, app, client, stored_part):
        response = client.delete(f"/box_maintenance/delete_part/{stored_part}")

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "Part 3001 removed from storage successfully."
        }
        with app.app_context():
            assert db.session.get(PartStorage, stored_part) is None

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
