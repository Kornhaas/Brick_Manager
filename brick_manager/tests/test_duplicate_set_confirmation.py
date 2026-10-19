"""Regression tests for duplicate-set warnings and confirmation."""

from unittest.mock import patch

from models import RebrickableSets, RebrickableThemes, User_Set, db


def _create_catalog_set(set_num="71512-1"):
    theme = RebrickableThemes(name="Dreamzzz")
    db.session.add(theme)
    db.session.flush()
    db.session.add(
        RebrickableSets(
            set_num=set_num,
            name="Crocodile Submarine",
            year=2026,
            theme_id=theme.id,
            num_parts=1110,
        )
    )
    db.session.commit()


def _add_copy(set_num="71512-1", status="sealed"):
    user_set = User_Set(set_num=set_num, status=status)
    db.session.add(user_set)
    db.session.commit()
    return user_set


def test_search_shows_existing_copies_and_confirmation_contract(client):
    _create_catalog_set()
    first = _add_copy(status="sealed")
    second = _add_copy(status="complete")

    response = client.post("/set_search", data={"set_number": "71512-1"})

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Already in your collection" in html
    assert "You already have 2" in html
    assert f"Box ID {first.id}" in html
    assert f"Box ID {second.id}" in html
    assert 'data-existing-count="2"' in html
    assert "Save another copy?" in html
    assert "button.disabled = true" in html


def test_duplicate_is_not_saved_without_confirmation(client):
    _create_catalog_set()
    _add_copy()

    response = client.post(
        "/add_set",
        data={"set_number": "71512-1", "status": "sealed"},
    )

    assert response.status_code == 302
    assert User_Set.query.filter_by(set_num="71512-1").count() == 1


def test_confirmed_duplicate_can_be_saved(client):
    _create_catalog_set()
    _add_copy()

    with (
        patch("routes.set_search.fetch_set_parts_info", return_value=[]),
        patch("routes.set_search.fetch_minifigs_info", return_value=[]),
    ):
        response = client.post(
            "/add_set",
            data={
                "set_number": "71512-1",
                "status": "sealed",
                "confirm_duplicate": "yes",
            },
        )

    assert response.status_code == 302
    copies = User_Set.query.filter_by(set_num="71512-1").order_by(User_Set.id).all()
    assert len(copies) == 2
    assert [copy.status for copy in copies] == ["sealed", "sealed"]
