"""Cross-table identities, safe batch updates and bounded collection-list reads."""

from contextlib import contextmanager
from unittest.mock import patch

import pytest
from flask import template_rendered
from models import (
    RebrickableMinifigs,
    User_Minifigures,
    User_Parts,
    UserMinifigurePart,
    db,
)
from sqlalchemy import event
from sqlalchemy.orm import Session

from brick_manager.tests.test_ui_contracts import (
    collection_records as _collection_records,
)


@pytest.fixture
def colliding_parts():
    user_set = _collection_records.__wrapped__()
    regular = User_Parts.query.filter_by(user_set_id=user_set.id).one()
    db.session.add(
        RebrickableMinifigs(fig_num="hardening-figure", name="Figure", num_parts=5)
    )
    db.session.flush()
    figure = User_Minifigures(
        fig_num="hardening-figure", quantity=1, user_set_id=user_set.id
    )
    db.session.add(figure)
    db.session.flush()
    minifig = UserMinifigurePart(
        id=regular.id,
        part_num=regular.part_num,
        color_id=regular.color_id,
        quantity=5,
        have_quantity=1,
        user_set_id=user_set.id,
        minifigure_id=figure.id,
    )
    db.session.add(minifig)
    db.session.commit()
    return regular.id, user_set.id


@contextmanager
def rendered_context(app):
    contexts = []

    def capture(sender, template, context, **extra):
        contexts.append(context)

    template_rendered.connect(capture, app)
    try:
        yield contexts
    finally:
        template_rendered.disconnect(capture, app)


def test_minifigure_update_cannot_modify_regular_row_with_same_id(
    client, colliding_parts
):
    part_id, _ = colliding_parts
    response = client.post(
        "/update_quantity",
        json={
            "changes": [{"part_id": part_id, "part_type": "minifig", "new_quantity": 3}]
        },
    )
    assert response.status_code == 200
    assert db.session.get(UserMinifigurePart, part_id).have_quantity == 3
    assert db.session.get(User_Parts, part_id).have_quantity == 4


def test_ambiguous_legacy_batch_fails_without_partial_mutation(client, colliding_parts):
    part_id, _ = colliding_parts
    other = User_Parts.query.filter(User_Parts.id != part_id).one()
    before = other.have_quantity
    response = client.post(
        "/update_quantity",
        json={
            "changes": [
                {"part_id": other.id, "new_quantity": 3},
                {"part_id": part_id, "new_quantity": 2},
            ]
        },
    )
    assert response.status_code == 409
    assert db.session.get(User_Parts, other.id).have_quantity == before
    assert db.session.get(User_Parts, part_id).have_quantity == 4
    assert db.session.get(UserMinifigurePart, part_id).have_quantity == 1


@pytest.mark.parametrize("part_type", ["wrong", True, 1, {}, None])
def test_invalid_explicit_quantity_types_rejected(client, colliding_parts, part_type):
    part_id, _ = colliding_parts
    response = client.post(
        "/update_quantity",
        json={
            "changes": [{"part_id": part_id, "part_type": part_type, "new_quantity": 2}]
        },
    )
    assert response.status_code == 400
    assert db.session.get(User_Parts, part_id).have_quantity == 4


def test_typed_mixed_batch_acknowledges_clamped_values(client, colliding_parts):
    part_id, _ = colliding_parts
    response = client.post(
        "/update_quantity",
        json={
            "changes": [
                {"part_id": part_id, "part_type": "regular", "new_quantity": 999},
                {"part_id": part_id, "part_type": "minifig", "new_quantity": -1},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json["updates"] == [
        {"part_id": part_id, "part_type": "regular", "have_quantity": 10},
        {"part_id": part_id, "part_type": "minifig", "have_quantity": 0},
    ]


def test_missing_target_aborts_the_complete_batch(client, colliding_parts):
    part_id, _ = colliding_parts
    response = client.post(
        "/update_quantity",
        json={
            "changes": [
                {"part_id": part_id, "part_type": "regular", "new_quantity": 8},
                {"part_id": 999999, "part_type": "regular", "new_quantity": 2},
            ]
        },
    )
    assert response.status_code == 404
    assert db.session.get(User_Parts, part_id).have_quantity == 4


def test_duplicate_batch_targets_are_rejected(client, colliding_parts):
    part_id, _ = colliding_parts
    response = client.post(
        "/update_quantity",
        json={
            "changes": [
                {"part_id": part_id, "part_type": "regular", "new_quantity": 8},
                {"part_id": part_id, "part_type": "regular", "new_quantity": 2},
            ]
        },
    )
    assert response.status_code == 400
    assert db.session.get(User_Parts, part_id).have_quantity == 4


def test_dashboard_dto_and_detail_inputs_include_part_type(client, colliding_parts):
    with patch("routes.dashboard.load_part_lookup", return_value={}):
        data = client.get("/api/missing_minifigure_parts").get_json()
        html = client.get("/details/missing_minifigure_parts").get_data(as_text=True)
    assert data[0]["part_type"] == "minifig"
    assert 'data-part-type="minifig"' in html


def test_set_list_keeps_theme_filter_separate_from_rendered_rows(
    app, client, colliding_parts
):
    with rendered_context(app) as contexts:
        response = client.get("/set_maintain")
    assert response.status_code == 200
    assert contexts[-1]["filters"]["theme"] == ""
    with rendered_context(app) as contexts:
        response = client.get("/set_maintain?theme=Space+%26+Science")
    assert response.status_code == 200
    assert contexts[-1]["filters"]["theme"] == "Space & Science"


def test_set_list_aggregates_without_loading_inventory_objects(
    app, client, colliding_parts
):
    _, set_id = colliding_parts
    db.session.expunge_all()
    loaded = []

    def observe(session, instance):
        if isinstance(instance, (User_Parts, UserMinifigurePart, User_Minifigures)):
            loaded.append(type(instance).__name__)

    event.listen(Session, "loaded_as_persistent", observe)
    try:
        with rendered_context(app) as contexts:
            response = client.get("/set_maintain")
    finally:
        event.remove(Session, "loaded_as_persistent", observe)
    assert response.status_code == 200
    row = next(
        entry
        for entry in contexts[-1]["sets_with_completeness"]
        if entry["user_set"].id == set_id
    )
    assert row["theme_name"] == "Space & Science"
    assert row["total_parts"] == 15 and row["parts_owned"] == 5
    assert row["completeness_percentage"] == 33.33
    assert loaded == [], f"List view loaded child entities unnecessarily: {loaded}"


@pytest.mark.parametrize(
    "change",
    [
        {"have_quantity": 1.9},
        {"have_quantity": "1.9"},
        {"part_id": 1.9},
        {"part_id": 2**64},
        {"part_type": "figure"},
        {"part_type": None},
        {"part_type": {}},
    ],
)
def test_single_quantity_write_rejects_ambiguous_or_truncated_values(
    client, colliding_parts, change
):
    part_id, _ = colliding_parts
    payload = {"part_id": part_id, "have_quantity": 2, "part_type": "regular", **change}
    response = client.post("/set_maintain/update_part_quantity", json=payload)
    assert response.status_code == 400
    assert db.session.get(User_Parts, part_id).have_quantity == 4
    assert db.session.get(UserMinifigurePart, part_id).have_quantity == 1


def test_single_quantity_write_preserves_integer_string_compatibility(
    client, colliding_parts
):
    part_id, _ = colliding_parts
    response = client.post(
        "/set_maintain/update_part_quantity",
        json={"part_id": str(part_id), "have_quantity": "8", "part_type": "regular"},
    )
    assert response.status_code == 200
    assert db.session.get(User_Parts, part_id).have_quantity == 8
