"""Navigation and transactional writes for a physical set copy."""

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from models import (
    PartStorage,
    RebrickableColors,
    RebrickableMinifigs,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    User_Minifigures,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SetCopy:
    id: int
    regular: int
    spare: int
    minifig: int

    @property
    def path(self):
        return f"/set_maintain/{self.id}/details"


class DetailMarkup(HTMLParser):
    def __init__(self, response):
        super().__init__()
        self.back_link = None
        self.inputs = {}
        self.rows = []
        self.feed(response.get_data(as_text=True))

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        element_id = fields.get("id", "")
        if tag == "a" and element_id == "set-back-link":
            self.back_link = fields["href"]
        if tag == "input" and "name" in fields:
            self.inputs[fields["name"]] = fields
        if tag == "tr" and element_id.startswith("set-box-"):
            self.rows.append(int(element_id.removeprefix("set-box-")))


def seed_set_copies():
    """Create two identical catalog sets with different physical inventories."""
    category = RebrickablePartCategories(name="Brick")
    red = RebrickableColors(id=5, name="Red", rgb="C91A09", is_trans=False)
    theme = RebrickableThemes(name="Space & Science")
    figure = RebrickableMinifigs(
        fig_num="fig-1",
        name="Pilot <img src=x onerror=alert(1)>",
        num_parts=1,
    )
    db.session.add_all([category, red, theme, figure])
    db.session.flush()
    template = RebrickableSets(
        set_num="1000-1",
        name="Explorer & Research",
        year=2024,
        theme_id=theme.id,
        num_parts=7,
    )
    parts = [
        RebrickableParts(part_num="3001", name="Brick 2 x 4", part_cat_id=category.id),
        RebrickableParts(part_num="3020", name="Spare tile", part_cat_id=category.id),
        RebrickableParts(
            part_num="970c00", name="A & B <legs>", part_cat_id=category.id
        ),
    ]
    db.session.add_all([template, *parts])
    db.session.flush()
    db.session.add(
        PartStorage(part_num=parts[-1].part_num, location="<shelf>", level="1", box="B")
    )

    copies = []
    for index, owned in enumerate((1, 4), start=1):
        user_set = User_Set(id=index, set_num=template.set_num, status="unknown")
        db.session.add(user_set)
        db.session.flush()
        user_minifigure = User_Minifigures(
            fig_num=figure.fig_num, quantity=1, user_set_id=user_set.id
        )
        db.session.add(user_minifigure)
        db.session.flush()
        regular = User_Parts(
            id=index,
            part_num=parts[0].part_num,
            color_id=red.id,
            user_set_id=user_set.id,
            quantity=5,
            have_quantity=owned,
        )
        spare = User_Parts(
            id=10 + index,
            part_num=parts[1].part_num,
            color_id=red.id,
            user_set_id=user_set.id,
            quantity=1,
            have_quantity=1,
            is_spare=True,
        )
        minifig = UserMinifigurePart(
            id=index,
            part_num=parts[2].part_num,
            color_id=red.id,
            user_set_id=user_set.id,
            minifigure_id=user_minifigure.id,
            quantity=2,
            have_quantity=0,
        )
        db.session.add_all([regular, spare, minifig])
        copies.append(SetCopy(user_set.id, regular.id, spare.id, minifig.id))

    db.session.commit()
    return tuple(copies)


@pytest.fixture
def copies():
    return seed_set_copies()


def inventory(copy):
    """Read the saved status and quantities through SQLite."""
    db.session.expire_all()
    return (
        db.session.scalar(select(User_Set.status).where(User_Set.id == copy.id)),
        db.session.scalar(
            select(User_Parts.have_quantity).where(User_Parts.id == copy.regular)
        ),
        db.session.scalar(
            select(User_Parts.have_quantity).where(User_Parts.id == copy.spare)
        ),
        db.session.scalar(
            select(UserMinifigurePart.have_quantity).where(
                UserMinifigurePart.id == copy.minifig
            )
        ),
    )


def test_detail_is_directly_addressable_and_preserves_legacy_json(client, copies):
    first, second = copies
    first_json = client.get(f"/set_maintain/{first.id}").get_json()
    second_json = client.get(f"/set_maintain/{second.id}").get_json()

    assert set(first_json) == {
        "set_img_url",
        "parts",
        "minifigs",
        "status",
        "completeness_percentage",
    }
    assert {part["id"]: part["have_quantity"] for part in first_json["parts"]} == {
        first.regular: 1,
        first.spare: 1,
    }
    assert {part["id"]: part["have_quantity"] for part in second_json["parts"]} == {
        second.regular: 4,
        second.spare: 1,
    }
    assert first_json["minifigs"][0]["parts"][0]["id"] == first.minifig
    assert second_json["minifigs"][0]["parts"][0]["id"] == second.minifig
    assert first_json["completeness_percentage"] == 25
    assert second_json["completeness_percentage"] == 62.5

    response = client.get(first.path)

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b"Explorer &amp; Research" in response.data
    assert b"1000-1" in response.data
    assert f'name="part_id_{first.regular}"'.encode() in response.data
    assert f'name="minifig_part_id_{first.minifig}"'.encode() in response.data
    assert f'name="part_id_{second.regular}"'.encode() not in response.data


def test_detail_catalog_strings_remain_text(client, copies):
    first, _ = copies
    db.session.get(RebrickableColors, 5).rgb = 'FFFFFF" onclick="alert(1)'
    db.session.commit()

    response = client.get(first.path)

    assert response.status_code == 200
    assert b"Pilot &lt;img src=x onerror=alert(1)&gt;" in response.data
    assert b"A &amp; B &lt;legs&gt;" in response.data
    assert b"&lt;shelf&gt;" in response.data
    assert b"<img src=x onerror=alert(1)>" not in response.data
    assert b'onclick="alert(1)' not in response.data


def test_json_save_uses_copy_and_inventory_type_as_identity(client, copies):
    first, second = copies
    assert first.regular == first.minifig
    values = {
        "status": "assembled",
        f"part_id_{first.regular}": 3,
        f"part_id_{first.spare}": 0,
        f"minifig_part_id_{first.minifig}": 2,
    }

    response = client.post(first.path, json=values)

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "status": "assembled",
        "values": values,
        "completeness_percentage": 62.5,
    }
    assert inventory(first) == ("assembled", 3, 0, 2)
    assert inventory(second) == ("unknown", 4, 1, 0)
    assert (
        client.get(f"/set_maintain/{first.id}").get_json()["completeness_percentage"]
        == 62.5
    )


def test_unassigned_minifigure_part_can_only_be_edited_in_owning_copy(client, copies):
    first, second = copies
    foreign_figure = User_Minifigures.query.filter_by(user_set_id=second.id).one()
    part = UserMinifigurePart(
        part_num="970c00",
        color_id=5,
        quantity=3,
        have_quantity=2,
        user_set_id=first.id,
        minifigure_id=foreign_figure.id,
    )
    db.session.add(part)
    db.session.commit()
    name = f"minifig_part_id_{part.id}"

    owned_detail = client.get(first.path)
    foreign_detail = client.get(second.path)
    assert owned_detail.status_code == foreign_detail.status_code == 200
    assert DetailMarkup(owned_detail).inputs[name]["value"] == "2"
    assert name not in DetailMarkup(foreign_detail).inputs
    for copy in (first, second):
        data = client.get(f"/set_maintain/{copy.id}").get_json()
        assert "unassigned_minifig_parts" not in data
        assert [item["id"] for item in data["minifigs"][0]["parts"]] == [copy.minifig]

    rejected = client.post(second.path, json={name: 0})
    assert rejected.status_code == 400
    assert db.session.get(UserMinifigurePart, part.id).have_quantity == 2
    saved = client.post(first.path, json={name: 3})
    assert saved.status_code == 200
    assert saved.get_json()["completeness_percentage"] == 45.45
    assert db.session.get(UserMinifigurePart, part.id).have_quantity == 3
    assert inventory(second) == ("unknown", 4, 1, 0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("minifig_part_id_2", 1),
        ("part_id_2", 1),
        ("minifig_part_id_11", 1),  # A real regular-part ID, in the wrong namespace.
        ("minifig_part_id_true", 1),
        ("minifig_part_id_1", True),
        ("minifig_part_id_1", "1.5"),
        ("minifig_part_id_1", 1.0),
        ("minifig_part_id_1", 3),
        ("minifig_part_id_1", -1),
        ("status", "packed"),
        ("user_set_id", 2),
    ],
)
def test_invalid_detail_write_leaves_both_copies_unchanged(
    client, copies, field, value
):
    first, second = copies
    payload = {"status": "assembled", f"part_id_{first.regular}": 3, field: value}

    response = client.post(first.path, json=payload)

    assert response.status_code == 400
    assert response.get_json()["success"] is False
    assert response.get_json()["error"]
    assert inventory(first) == ("unknown", 1, 1, 0)
    assert inventory(second) == ("unknown", 4, 1, 0)


@pytest.mark.parametrize("body", ["", "{", "null", "[]", "{}"])
def test_detail_rejects_empty_or_malformed_json(client, copies, body):
    first, _ = copies

    response = client.post(first.path, data=body, content_type="application/json")

    assert response.status_code == 400
    assert response.get_json()["success"] is False
    assert inventory(first) == ("unknown", 1, 1, 0)


def test_detail_rejects_repeated_field_names(client, copies):
    first, _ = copies
    json_response = client.post(
        first.path,
        data='{"status":"assembled","part_id_1":2,"part_id_1":3}',
        content_type="application/json",
    )
    form_response = client.post(
        first.path,
        data="status=assembled&part_id_1=2&part_id_1=3",
        content_type="application/x-www-form-urlencoded",
    )

    assert json_response.status_code == form_response.status_code == 400
    assert json_response.get_json()["success"] is False
    assert inventory(first) == ("unknown", 1, 1, 0)


def test_failed_transaction_rolls_back_writes(client, copies, monkeypatch):
    first, second = copies

    def fail_commit(session):
        session.flush()
        raise OperationalError("COMMIT", {}, RuntimeError("simulated failure"))

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = client.post(
        first.path,
        json={
            "status": "assembled",
            f"part_id_{first.regular}": 3,
            f"minifig_part_id_{first.minifig}": 2,
        },
    )

    assert response.status_code == 409
    assert response.get_json()["success"] is False
    assert "simulated failure" not in response.get_data(as_text=True)
    assert inventory(first) == ("unknown", 1, 1, 0)
    assert inventory(second) == ("unknown", 4, 1, 0)


def test_form_save_redirects_to_same_copy_and_preserves_return_context(client, copies):
    first, second = copies
    source = "/set_maintain?q=Explorer&theme=Space+%26+Science&sort=set_name"
    response = client.post(
        first.path,
        query_string={"return_to": source},
        data={"status": "sealed", f"part_id_{first.regular}": "2"},
    )

    assert response.status_code == 303
    redirect = urlsplit(response.headers["Location"])
    assert (redirect.scheme, redirect.netloc, redirect.path) == ("", "", first.path)
    assert inventory(first) == ("sealed", 2, 1, 0)
    assert inventory(second) == ("unknown", 4, 1, 0)

    detail = client.get(response.headers["Location"])
    markup = DetailMarkup(detail)
    back_query = parse_qs(urlsplit(markup.back_link).query)
    assert back_query["q"] == ["Explorer"]
    assert back_query["theme"] == ["Space & Science"]
    assert back_query["sort"] == ["set_name"]
    assert markup.inputs[f"part_id_{first.regular}"]["value"] == "2"


def test_invalid_form_retains_values_without_committing(client, copies):
    first, _ = copies
    response = client.post(
        first.path,
        data={
            "status": "assembled",
            f"part_id_{first.regular}": "3",
            f"minifig_part_id_{first.minifig}": "9",
        },
    )

    assert response.status_code == 400
    assert "Location" not in response.headers
    draft = DetailMarkup(response).inputs
    assert draft[f"part_id_{first.regular}"]["value"] == "3"
    assert draft[f"minifig_part_id_{first.minifig}"]["value"] == "9"
    assert inventory(first) == ("unknown", 1, 1, 0)


@pytest.mark.parametrize(
    "destination",
    [
        "https://example.test/set_maintain",
        "//example.test/set_maintain",
        "/warehouse?next=https://example.test",
    ],
)
def test_detail_ignores_non_collection_return_targets(client, copies, destination):
    first, _ = copies

    response = client.get(first.path, query_string={"return_to": destination})

    assert response.status_code == 200
    assert DetailMarkup(response).back_link == "/set_maintain"


def test_detail_rebuilds_only_supported_return_parameters(client, copies):
    first, _ = copies
    expected = {
        "q": "Explorer & Research",
        "box_id": str(first.id),
        "theme": "Space & Science",
        "status": "unknown",
        "label": "not-printed",
        "completion": "incomplete",
        "group": "theme",
        "sort": "set_name",
        "direction": "asc",
        "per_page": "25",
        "page": "2",
    }
    raw = {
        **expected,
        "next": "https://example.test",
        "returned_box": "9999",
    }

    detail = client.get(
        first.path, query_string={"return_to": "/set_maintain?" + urlencode(raw)}
    )

    assert detail.status_code == 200
    target = urlsplit(DetailMarkup(detail).back_link)
    assert (target.scheme, target.netloc, target.path, target.fragment) == (
        "",
        "",
        "/set_maintain",
        f"set-box-{first.id}",
    )
    assert parse_qs(target.query) == {
        key: [value]
        for key, value in {**expected, "returned_box": str(first.id)}.items()
    }


def test_detail_rejects_nonexistent_copy(client):
    assert client.get("/set_maintain/999/details").status_code == 404
    assert (
        client.post("/set_maintain/999/details", json={"status": "unknown"}).status_code
        == 404
    )


def test_collection_sorts_globally_and_uses_stable_tie_breaks(client, copies):
    first, second = copies
    # Insert the highest set name last to separate catalog order from box IDs.
    template = db.session.get(RebrickableSets, "1000-1")
    db.session.add(
        RebrickableSets(
            set_num="1001-1",
            name="Zulu",
            year=template.year,
            theme_id=template.theme_id,
            num_parts=0,
        )
    )
    db.session.flush()
    db.session.add_all(User_Set(id=i, set_num=template.set_num) for i in range(3, 27))
    db.session.add(User_Set(id=27, set_num="1001-1"))
    db.session.commit()
    sorting = {"sort": "set_name", "direction": "asc", "per_page": 25}
    page_one = client.get("/set_maintain", query_string=sorting)
    page_two = client.get("/set_maintain", query_string={**sorting, "page": 2})

    assert page_one.status_code == page_two.status_code == 200
    first_rows = DetailMarkup(page_one).rows
    second_rows = DetailMarkup(page_two).rows
    assert len(first_rows) == 25
    assert len(second_rows) == 2
    assert 27 not in first_rows
    assert second_rows[-1] == 27
    assert sorted(first_rows + second_rows) == list(range(first.id, 28))
    assert second.id in first_rows + second_rows
    assert (
        DetailMarkup(client.get("/set_maintain", query_string=sorting)).rows
        == first_rows
    )


def test_return_to_now_filtered_out_copy_clamps_to_last_valid_page(client, copies):
    first, _ = copies
    db.session.add_all(User_Set(set_num="1000-1", status="unknown") for _ in range(24))
    db.session.commit()
    source = (
        "/set_maintain?status=unknown&sort=box_id&direction=desc&per_page=25&page=2"
    )
    detail = client.get(first.path, query_string={"return_to": source})
    back_link = DetailMarkup(detail).back_link
    assert DetailMarkup(client.get(source)).rows == [first.id]

    saved = client.post(first.path, json={"status": "sealed"})
    assert saved.status_code == 200
    returned = client.get(back_link, follow_redirects=True)

    assert returned.status_code == 200
    assert first.id not in DetailMarkup(returned).rows
    assert len(DetailMarkup(returned).rows) == 25
    assert b'id="return-notice"' in returned.data
    assert b"25 matching sets" in returned.data
    assert b'<option value="unknown" selected' in returned.data
