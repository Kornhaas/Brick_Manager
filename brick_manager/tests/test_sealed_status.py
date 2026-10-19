"""Regression tests for sealed user sets."""

from unittest.mock import patch

from models import (
    FULL_OWNERSHIP_STATUSES,
    NON_LOOSE_PART_STATUSES,
    RebrickablePartCategories,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    db,
)


def _create_user_set(status="unknown"):
    theme = RebrickableThemes(name="Test theme")
    db.session.add(theme)
    db.session.flush()
    template_set = RebrickableSets(
        set_num="10283-1",
        name="NASA Space Shuttle Discovery",
        year=2021,
        theme_id=theme.id,
        num_parts=2354,
    )
    db.session.add(template_set)
    db.session.flush()
    user_set = User_Set(set_num=template_set.set_num, status=status)
    db.session.add(user_set)
    db.session.commit()
    return user_set.id


def test_sealed_status_has_expected_inventory_semantics():
    assert "sealed" in FULL_OWNERSHIP_STATUSES
    assert "sealed" in NON_LOOSE_PART_STATUSES


def test_set_maintenance_renders_and_filters_sealed_status(client):
    _create_user_set(status="sealed")

    response = client.get("/set_maintain")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '<option value="sealed">Sealed</option>' in html
    assert "status-sealed" in html
    assert "Sealed" in html


def test_existing_set_can_be_updated_to_sealed(client):
    user_set_id = _create_user_set()

    response = client.post(
        "/set_maintain/update",
        data={"user_set_id": user_set_id, "status": "sealed"},
    )

    assert response.status_code == 302
    assert db.session.get(User_Set, user_set_id).status == "sealed"


def test_set_search_result_offers_save_as_sealed(client):
    _create_user_set()

    response = client.post("/set_search", data={"set_number": "10283-1"})

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Save Sealed" in html
    assert 'onclick="saveAsSealed(event)"' in html
    assert 'submitSet("sealed")' in html


def test_new_sealed_set_marks_inventory_as_owned(client):
    theme = RebrickableThemes(name="Test theme")
    category = RebrickablePartCategories(name="Brick")
    db.session.add_all([theme, category])
    db.session.flush()
    db.session.add(
        RebrickableSets(
            set_num="21318-1",
            name="Tree House",
            year=2019,
            theme_id=theme.id,
            num_parts=3036,
        )
    )
    db.session.commit()

    part = {
        "part_num": "3001",
        "name": "Brick 2 x 4",
        "category": category.id,
        "color": "Red",
        "color_rgb": "C91A09",
        "quantity": 4,
        "is_spare": False,
        "part_img_url": "https://example.test/3001.png",
    }
    with (
        patch("routes.set_search.fetch_set_parts_info", return_value=[part]),
        patch("routes.set_search.fetch_minifigs_info", return_value=[]),
    ):
        response = client.post(
            "/add_set",
            data={"set_number": "21318-1", "status": "sealed"},
        )

    assert response.status_code == 302
    user_set = User_Set.query.filter_by(set_num="21318-1").one()
    user_part = User_Parts.query.filter_by(user_set_id=user_set.id).one()
    assert user_set.status == "sealed"
    assert user_part.have_quantity == user_part.quantity == 4
