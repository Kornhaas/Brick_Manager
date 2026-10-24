"""Error-response contracts for the authenticated desktop API."""

from unittest.mock import MagicMock, patch

import pytest
from models import RebrickablePartCategories, RebrickableParts, db
from sqlalchemy.exc import SQLAlchemyError

API_KEY = "test-client-api-key"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


@pytest.mark.parametrize(
    "payload",
    [None, [], {"have_quantity": True}, {"have_quantity": "8"}],
)
def test_update_quantity_rejects_non_integer_json_values(client, payload):
    response = client.put(
        "/api/v1/user-parts/1/quantity", headers=HEADERS, json=payload
    )
    assert response.status_code == 400


def test_update_quantity_returns_not_found_for_unknown_user_part(client):
    response = client.put(
        "/api/v1/user-parts/999999/quantity",
        headers=HEADERS,
        json={"have_quantity": 1},
    )
    assert response.status_code == 404


def test_update_storage_rejects_unknown_part(client):
    response = client.put(
        "/api/v1/parts/unknown/storage",
        headers=HEADERS,
        json={"location": "Shelf A"},
    )
    assert response.status_code == 404


def test_update_storage_rejects_oversized_text(client):
    category = RebrickablePartCategories(name="Brick")
    db.session.add(category)
    db.session.flush()
    db.session.add(
        RebrickableParts(part_num="3001", name="Brick 2 x 4", part_cat_id=category.id)
    )
    db.session.commit()

    response = client.put(
        "/api/v1/parts/3001/storage",
        headers=HEADERS,
        json={"location": "x" * 201},
    )
    assert response.status_code == 400


@pytest.mark.parametrize(
    ("path", "payload", "message"),
    [
        (
            "/api/v1/user-parts/1/quantity",
            {"have_quantity": 1},
            "Unable to update user part",
        ),
        (
            "/api/v1/parts/3001/storage",
            {"location": "Shelf A"},
            "Unable to update storage",
        ),
    ],
)
def test_write_failure_rolls_back_and_hides_database_details(
    client, path, payload, message
):
    if "3001" in path:
        category = RebrickablePartCategories(name="Brick")
        db.session.add(category)
        db.session.flush()
        db.session.add(
            RebrickableParts(
                part_num="3001", name="Brick 2 x 4", part_cat_id=category.id
            )
        )
        db.session.commit()

    commit = patch.object(
        db.session, "commit", side_effect=SQLAlchemyError("database unavailable")
    )
    rollback = patch.object(db.session, "rollback")
    user_part = patch.object(
        db.session, "get", return_value=MagicMock(id=1, quantity=5, have_quantity=0)
    )
    with commit, rollback as mocked_rollback, user_part:
        response = client.put(path, headers=HEADERS, json=payload)

    assert response.status_code == 500
    assert response.json == {"error": message}
    mocked_rollback.assert_called_once()
