"""Color grouping and inventory status must describe the owning copy's rows."""

from html.parser import HTMLParser

import pytest
from models import RebrickableColors, User_Parts, db

from brick_manager.tests.test_set_detail import seed_set_copies


class ColorMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.groups = []
        self.details = []
        self.rows = {}
        self.swatches = []
        self.row = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "details":
            self.details.append(attrs)
            if "data-color-group" in attrs:
                self.groups.append(attrs)
        if "color-swatch" in attrs.get("class", "").split():
            self.swatches.append(attrs)
        if tag == "tr" and "data-part-row" in attrs:
            self.row = attrs
        if tag == "input" and "data-required" in attrs:
            self.rows[attrs["name"]] = {
                "row": self.row,
                "groups": [
                    group for group in self.details if "data-color-group" in group
                ],
            }

    def handle_endtag(self, tag):
        if tag == "details":
            self.details.pop()
        if tag == "tr":
            self.row = None


def seed_colored_copies():
    first, second = seed_set_copies()
    db.session.add(RebrickableColors(id=0, name="Black", rgb="05131D", is_trans=False))
    db.session.add_all(
        [
            User_Parts(
                id=90,
                part_num="3001",
                color_id=0,
                user_set_id=first.id,
                quantity=2,
                have_quantity=2,
            ),
            User_Parts(
                id=91,
                part_num="3020",
                color_id=0,
                user_set_id=first.id,
                quantity=3,
                have_quantity=0,
            ),
        ]
    )
    db.session.commit()
    return first, second


@pytest.fixture
def colored_copy():
    return seed_colored_copies()


def test_color_groups_keep_regular_spare_and_figure_ownership(client, colored_copy):
    first, second = colored_copy
    page = ColorMarkup(client.get(first.path).get_data(as_text=True))
    assert len(page.groups) == 4  # regular Black/Red, spare Red, figure Red
    assert len({group["data-color-group"] for group in page.groups}) == 4
    assert all("open" in group for group in page.groups)
    black = page.rows["part_id_90"]["groups"]
    assert len(black) == 1
    assert black[0]["data-color-name"] == "Black"
    assert page.rows["part_id_91"]["groups"] == black
    assert (
        page.rows[f"part_id_{first.regular}"]["groups"][0]["data-color-name"] == "Red"
    )
    assert page.rows[f"minifig_part_id_{first.minifig}"]["groups"] != black
    assert f"part_id_{second.regular}" not in page.rows
    assert len(page.rows) == 5


def test_complete_and_mismatched_rows_have_distinct_states(client, colored_copy):
    first, _ = colored_copy
    response = client.get(first.path)
    rows = ColorMarkup(response.get_data(as_text=True)).rows
    assert rows["part_id_90"]["row"]["data-quantity-state"] == "complete"
    assert rows["part_id_91"]["row"]["data-quantity-state"] == "missing"
    assert rows[f"part_id_{first.spare}"]["row"]["data-quantity-state"] == "complete"
    assert (
        rows[f"minifig_part_id_{first.minifig}"]["row"]["data-quantity-state"]
        == "missing"
    )
    assert "Vollständig" in response.get_data(as_text=True)
    assert "fehlen" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "rgb", ["C91A09", "abcdef", 'FFFFFF" onclick="alert(1)', "fff;display:none", ""]
)
def test_swatch_uses_only_valid_hex_and_indicates_transparency(
    client, colored_copy, rgb
):
    first, _ = colored_copy
    color = db.session.get(RebrickableColors, 5)
    color.rgb = rgb
    color.is_trans = True
    db.session.commit()
    page = ColorMarkup(client.get(first.path).get_data(as_text=True))
    red = [swatch for swatch in page.swatches if swatch.get("data-color-name") == "Red"]
    assert red
    assert all("color-translucent" in item["class"] for item in red)
    if rgb in {"C91A09", "abcdef"}:
        assert all(item["style"] == f"--swatch-color: #{rgb.upper()}" for item in red)
    else:
        assert all("style" not in item for item in red)
        assert all("color-unknown" in item["class"] for item in red)


def test_invalid_form_draft_is_not_marked_complete(client, colored_copy):
    first, _ = colored_copy
    response = client.post(first.path, data={"part_id_90": "3"})
    assert response.status_code == 400
    row = ColorMarkup(response.get_data(as_text=True)).rows["part_id_90"]["row"]
    assert row["data-quantity-state"] == "invalid"
    assert db.session.get(User_Parts, 90).have_quantity == 2
