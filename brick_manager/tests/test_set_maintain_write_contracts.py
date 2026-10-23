"""Write contracts for set-maintenance JSON endpoints."""

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


@pytest.fixture
def maintained_records():
    category = RebrickablePartCategories(name="Brick")
    color = RebrickableColors(id=5, name="Red", rgb="C91A09", is_trans=False)
    theme = RebrickableThemes(name="Space")
    db.session.add_all([category, color, theme])
    db.session.flush()
    part = RebrickableParts(
        part_num="3001", name="Brick 2 x 4", part_cat_id=category.id
    )
    template = RebrickableSets(
        set_num="1000-1",
        name="Test Set",
        year=2024,
        theme_id=theme.id,
        num_parts=5,
    )
    db.session.add_all([part, template])
    db.session.flush()
    user_set = User_Set(set_num=template.set_num, label_printed=False)
    db.session.add(user_set)
    db.session.flush()
    user_part = User_Parts(
        part_num=part.part_num,
        color_id=color.id,
        quantity=5,
        have_quantity=1,
        user_set_id=user_set.id,
    )
    db.session.add(user_part)
    db.session.commit()
    return user_set, user_part


def test_quantity_update_clamps_and_persists(client, maintained_records):
    _, user_part = maintained_records

    response = client.post(
        "/set_maintain/update_part_quantity",
        json={"part_id": user_part.id, "part_type": "regular", "have_quantity": 99},
    )

    assert response.status_code == 200
    assert response.get_json()["have_quantity"] == 5
    assert db.session.get(User_Parts, user_part.id).have_quantity == 5


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"part_id": True, "have_quantity": 1},
        {"part_id": 1, "have_quantity": True},
    ],
)
def test_quantity_update_rejects_malformed_payload(client, payload):
    response = client.post("/set_maintain/update_part_quantity", json=payload)

    assert response.status_code == 400
    assert response.get_json() == {"success": False, "message": "Invalid input value"}


def test_label_status_requires_a_real_boolean(client, maintained_records):
    user_set, _ = maintained_records

    response = client.post(
        "/set_maintain/update_label_status",
        json={"user_set_id": user_set.id, "label_printed": "false"},
    )

    assert response.status_code == 400
    assert db.session.get(User_Set, user_set.id).label_printed is False


def test_label_status_persists_boolean(client, maintained_records):
    user_set, _ = maintained_records

    response = client.post(
        "/set_maintain/update_label_status",
        json={"user_set_id": user_set.id, "label_printed": True},
    )

    assert response.status_code == 200
    assert db.session.get(User_Set, user_set.id).label_printed is True
