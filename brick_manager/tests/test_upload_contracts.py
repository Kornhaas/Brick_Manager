"""Behavioral contracts for accepted upload filenames."""

from io import BytesIO
from pathlib import Path

import pytest
from models import (
    RebrickableColors,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    db,
)
from routes.upload import allowed_file, save_uploaded_file
from werkzeug.datastructures import FileStorage


@pytest.mark.parametrize(
    ("filename", "accepted"),
    [
        ("part.png", True),
        ("part.JPG", True),
        ("animated-part.gif", True),
        ("legacy-part.gi", True),
        ("part.svg", False),
        ("part", False),
        (".gif", True),
    ],
)
def test_allowed_file_uses_the_documented_image_extensions(filename, accepted):
    """GIF uploads work while preserving the historical ``.gi`` allowance."""
    assert allowed_file(filename) is accepted


def test_save_uploaded_file_generates_unique_safe_names(tmp_path, monkeypatch):
    """Same-named uploads do not overwrite one another on disk."""
    monkeypatch.setattr("routes.upload.Config.UPLOAD_FOLDER", str(tmp_path))
    first = FileStorage(stream=BytesIO(b"first"), filename="../part.gif")
    second = FileStorage(stream=BytesIO(b"second"), filename="../part.gif")

    first_path, first_name = save_uploaded_file(first)
    second_path, second_name = save_uploaded_file(second)

    assert first_name != second_name
    assert first_name.endswith(".gif")
    assert second_name.endswith(".gif")
    assert Path(first_path).read_bytes() == b"first"
    assert Path(second_path).read_bytes() == b"second"


def test_save_uploaded_file_rejects_a_filename_without_safe_content(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("routes.upload.Config.UPLOAD_FOLDER", str(tmp_path))
    upload = FileStorage(stream=BytesIO(b"data"), filename="../../")

    with pytest.raises(OSError, match="empty after sanitization"):
        save_uploaded_file(upload)


@pytest.fixture
def upload_user_part():
    category = RebrickablePartCategories(name="Brick")
    color = RebrickableColors(id=7, name="Blue", rgb="0055BF", is_trans=False)
    theme = RebrickableThemes(name="City")
    db.session.add_all([category, color, theme])
    db.session.flush()
    part = RebrickableParts(part_num="3002", name="Brick", part_cat_id=category.id)
    template = RebrickableSets(
        set_num="2000-1", name="Upload Set", year=2025, theme_id=theme.id, num_parts=3
    )
    db.session.add_all([part, template])
    db.session.flush()
    user_set = User_Set(set_num=template.set_num)
    db.session.add(user_set)
    db.session.flush()
    user_part = User_Parts(
        part_num=part.part_num,
        color_id=color.id,
        quantity=3,
        have_quantity=1,
        user_set_id=user_set.id,
    )
    db.session.add(user_part)
    db.session.commit()
    return user_part


def test_increment_part_persists_quantity(client, upload_user_part):
    response = client.post(f"/upload/increment_part/{upload_user_part.id}")

    assert response.status_code == 200
    assert response.get_json()["new_have"] == 2
    assert db.session.get(User_Parts, upload_user_part.id).have_quantity == 2


@pytest.mark.parametrize("payload", [None, [], {"have_quantity": True}])
def test_update_part_quantity_rejects_malformed_json(client, upload_user_part, payload):
    response = client.post(
        f"/upload/update_part_quantity/{upload_user_part.id}", json=payload
    )

    assert response.status_code == 400
    assert db.session.get(User_Parts, upload_user_part.id).have_quantity == 1


@pytest.mark.parametrize("quantity", [-1, 4])
def test_update_part_quantity_enforces_bounds(client, upload_user_part, quantity):
    response = client.post(
        f"/upload/update_part_quantity/{upload_user_part.id}",
        json={"have_quantity": quantity},
    )

    assert response.status_code == 400
    assert db.session.get(User_Parts, upload_user_part.id).have_quantity == 1


def test_update_part_quantity_persists_valid_value(client, upload_user_part):
    response = client.post(
        f"/upload/update_part_quantity/{upload_user_part.id}",
        json={"have_quantity": 3},
    )

    assert response.status_code == 200
    assert response.get_json()["new_missing"] == 0
    assert db.session.get(User_Parts, upload_user_part.id).have_quantity == 3


@pytest.mark.parametrize("payload", [None, [], {}, {"part_num": "3002"}])
def test_storage_location_rejects_incomplete_payload(client, payload):
    response = client.post("/upload/save_storage_location", json=payload)

    assert response.status_code == 400
    assert response.get_json()["success"] is False
