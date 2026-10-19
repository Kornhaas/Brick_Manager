"""Regression tests for deleting a user set from set maintenance."""

from models import RebrickableSets, RebrickableThemes, User_Set, db


def _create_user_set(set_num="363-1"):
    theme = RebrickableThemes(name="Test theme")
    db.session.add(theme)
    db.session.flush()

    template_set = RebrickableSets(
        set_num=set_num,
        name="Test Set",
        year=1975,
        theme_id=theme.id,
        num_parts=32,
    )
    db.session.add(template_set)
    db.session.flush()

    user_set = User_Set(set_num=set_num)
    db.session.add(user_set)
    db.session.commit()
    return user_set.id


def test_set_maintenance_renders_delete_as_post_form(client):
    user_set_id = _create_user_set()

    response = client.get("/set_maintain")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f'action="/set_maintain/delete/{user_set_id}"' in html
    assert 'class="delete-form"' in html
    assert 'method="post"' in html
    assert 'type="submit"' in html


def test_delete_user_set_removes_record_and_redirects(client):
    user_set_id = _create_user_set()

    response = client.post(f"/set_maintain/delete/{user_set_id}")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/set_maintain")
    assert db.session.get(User_Set, user_set_id) is None
