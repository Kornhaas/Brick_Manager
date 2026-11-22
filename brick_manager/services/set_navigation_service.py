"""Validated list context and stable, collection-wide Set Maintenance ordering."""

from urllib.parse import parse_qsl, urlsplit

from flask import url_for
from models import (
    USER_SET_STATUSES,
    RebrickableSets,
    RebrickableThemes,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from sqlalchemy import func

from services.collection_quantity_service import parse_integer

LIST_ENDPOINT = "set_maintain.set_maintain"
SORT_KEYS = {
    "set_num",
    "set_name",
    "theme",
    "box_id",
    "parts",
    "status",
    "label_printed",
}
DEFAULT_FILTERS = {
    "q": "",
    "box_id": None,
    "status": "",
    "theme": "",
    "label": "",
    "completion": "",
    "group": "",
    "page": 1,
    "per_page": 50,
    "sort": "box_id",
    "direction": "desc",
}


def positive_number(value):
    try:
        return parse_integer(value, positive_id=True)
    except ValueError:
        return None


def list_parameters(args):
    """Keep only supported, typed query parameters when constructing internal links."""
    values = {}
    for name in ("q", "theme"):
        value = args.get(name, "").strip()
        if value:
            values[name] = value
    for name, allowed in (
        ("status", USER_SET_STATUSES),
        ("label", {"printed", "not-printed"}),
        ("completion", {"incomplete", "complete", "no-parts"}),
        ("group", {"theme"}),
        ("sort", SORT_KEYS),
        ("direction", {"asc", "desc"}),
    ):
        value = args.get(name)
        if value in allowed:
            values[name] = value
    for name in ("box_id", "page", "per_page"):
        number = positive_number(args.get(name))
        if number is None:
            continue
        if name == "page" and number > 2**31 - 1:
            continue
        if name == "per_page" and number not in {25, 50, 100}:
            continue
        values[name] = number
    return values


def details_navigation(copy_id, return_to):
    """Build both navigation targets from local routes. Direct links use the plain list."""
    list_url = url_for(LIST_ENDPOINT)
    detail_values = {"user_set_id": copy_id}
    if return_to and not return_to.startswith("//") and return_to.startswith(list_url):
        try:
            origin = urlsplit(return_to)
            if not origin.scheme and not origin.netloc and origin.path == list_url:
                params = list_parameters(dict(parse_qsl(origin.query)))
                detail_values["return_to"] = url_for(LIST_ENDPOINT, **params)
                list_url = url_for(
                    LIST_ENDPOINT,
                    **params,
                    returned_box=copy_id,
                    _anchor=f"set-box-{copy_id}",
                )
        except ValueError:
            pass
    return list_url, url_for("set_maintain.set_details", **detail_values)


def order_sets(query, sort, direction, group):
    columns = {
        "set_num": RebrickableSets.set_num.collate("NOCASE"),
        "set_name": RebrickableSets.name.collate("NOCASE"),
        "theme": RebrickableThemes.name.collate("NOCASE"),
        "box_id": User_Set.id,
        "status": User_Set.status,
        "label_printed": User_Set.label_printed,
    }
    if group == "theme" or sort == "theme":
        query = query.outerjoin(RebrickableSets.theme)
    if group == "theme" and sort != "theme":
        query = query.order_by(RebrickableThemes.name)
    if sort == "parts":
        totals = []
        for model in (User_Parts, UserMinifigurePart):
            summary = (
                db.session.query(
                    model.user_set_id, func.sum(model.quantity).label("required")
                )
                .group_by(model.user_set_id)
                .subquery()
            )
            query = query.outerjoin(summary, User_Set.id == summary.c.user_set_id)
            totals.append(func.coalesce(summary.c.required, 0))
        column = totals[0] + totals[1]
    else:
        column = columns[sort]
    primary = column.asc() if direction == "asc" else column.desc()
    if group == "theme" and sort == "theme":
        # Themes whose names differ only by case still need contiguous section headers.
        exact = RebrickableThemes.name
        exact_order = exact.asc() if direction == "asc" else exact.desc()
        return query.order_by(primary, exact_order, User_Set.id.desc())
    return query.order_by(primary, User_Set.id.desc())
