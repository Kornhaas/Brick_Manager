"""Behavioral contracts for the part-location UI and JSON endpoints."""

from unittest.mock import patch


def test_part_location_get_renders_sorted_categories(client):
    with (
        patch(
            "routes.part_location.RebrickableService.get_all_category_ids",
            return_value=[(2, "Technic"), (1, "Brick")],
        ),
        patch("routes.part_location.load_part_lookup", return_value={}),
    ):
        response = client.get("/part_location")

    assert response.status_code == 200
    assert response.data.index(b"Brick") < response.data.index(b"Technic")


def test_part_location_hides_service_exception_details(client):
    with patch(
        "routes.part_location.RebrickableService.get_all_category_ids",
        side_effect=RuntimeError("private upstream detail"),
    ):
        response = client.get("/part_location")

    assert response.status_code == 500
    assert b"Unable to load part-location data." in response.data
    assert b"private upstream detail" not in response.data


def test_save_locations_merges_existing_lookup(client):
    lookup = {"3001": {"location": "A", "level": "1"}}
    with (
        patch("routes.part_location.load_part_lookup", return_value=lookup),
        patch("routes.part_location.save_part_lookup") as save_lookup,
    ):
        response = client.post(
            "/save_locations",
            json={"3001": {"box": "7"}, "3002": {"location": "B"}},
        )

    assert response.status_code == 200
    save_lookup.assert_called_once_with(
        {
            "3001": {"location": "A", "level": "1", "box": "7"},
            "3002": {"location": "B"},
        }
    )


def test_save_locations_rejects_non_object_json(client):
    response = client.post("/save_locations", json=[])

    assert response.status_code == 400
    assert response.get_json() == {"error": "An error occurred while saving locations."}


def test_delete_location_persists_removal(client):
    lookup = {"3001": {"location": "A"}}
    with (
        patch("routes.part_location.load_part_lookup", return_value=lookup),
        patch("routes.part_location.save_part_lookup") as save_lookup,
    ):
        response = client.post("/delete_location", json={"part_num": "3001"})

    assert response.status_code == 200
    save_lookup.assert_called_once_with({})


def test_delete_location_reports_missing_part(client):
    with patch("routes.part_location.load_part_lookup", return_value={}):
        response = client.post("/delete_location", json={"part_num": "unknown"})

    assert response.status_code == 404


def test_create_label_returns_generated_path(client):
    with patch(
        "routes.part_location.create_label_image", return_value="/labels/3001.png"
    ) as create_label:
        response = client.post("/create_label", json={"part_num": "3001"})

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "image_path": "/labels/3001.png",
    }
    create_label.assert_called_once_with({"part_num": "3001"})
