"""Read and edit the inventory belonging to one physical set copy."""

from collections import defaultdict

from models import (
    USER_SET_STATUSES,
    PartStorage,
    RebrickableInventories,
    RebrickableInventoryParts,
    User_Parts,
    UserMinifigurePart,
    db,
)
from sqlalchemy import func

from services.collection_quantity_service import parse_integer


def _storage_by_number(copy_id):
    numbers = (
        db.session.query(User_Parts.part_num)
        .filter_by(user_set_id=copy_id)
        .union(
            db.session.query(UserMinifigurePart.part_num).filter_by(user_set_id=copy_id)
        )
    )
    locations = {}
    for row in (
        PartStorage.query.filter(PartStorage.part_num.in_(numbers))
        .order_by(PartStorage.id)
        .all()
    ):
        locations.setdefault(row.part_num, row)
    return locations


def _inventory_images(set_numbers):
    # Match the first catalog inventory for each set or figure, as in the JSON view.
    inventories = (
        db.session.query(
            RebrickableInventories.set_num,
            func.min(RebrickableInventories.id).label("inventory_id"),
        )
        .filter(RebrickableInventories.set_num.in_(set_numbers))
        .group_by(RebrickableInventories.set_num)
        .subquery()
    )
    rows = (
        db.session.query(
            inventories.c.set_num,
            RebrickableInventoryParts.part_num,
            RebrickableInventoryParts.color_id,
            RebrickableInventoryParts.img_url,
        )
        .join(
            RebrickableInventoryParts,
            RebrickableInventoryParts.inventory_id == inventories.c.inventory_id,
        )
        .order_by(RebrickableInventoryParts.is_spare)
        .all()
    )
    images = defaultdict(dict)
    for number, part_num, color_id, url in rows:
        images[number].setdefault((part_num, color_id), url)
    return images


def _display_part(part, storage, image):
    catalog = part.rebrickable_part
    color = part.rebrickable_color
    return {
        "id": part.id,
        "part_num": part.part_num,
        "name": catalog.name if catalog else "Unknown",
        "category": catalog.category.name
        if catalog and catalog.category
        else "Unknown Category",
        "quantity": part.quantity,
        "have_quantity": part.have_quantity or 0,
        "color": color.name if color else "Unknown",
        "color_rgb": color.rgb if color else "FFFFFF",
        "part_img_url": image,
        "location": f"Location: {storage.location if storage else 'Unknown'}, "
        f"Level: {storage.level if storage else 'Unknown'}, "
        f"Box: {storage.box if storage else 'Unknown'}",
        "status": "Available" if storage else "Not Available",
        "is_spare": part.is_spare,
    }


def _sort_parts(parts):
    parts.sort(
        key=lambda item: (item["color"], item["category"], item["name"], item["id"])
    )
    return parts


def completeness_percentage(owned, required):
    return round((owned / required) * 100, 2) if required else 0


def inventory_details(user_set, *, include_unassigned=False):
    """Build the shared HTML/JSON read model with collection-wide lookups per copy."""
    figures = user_set.minifigures_in_set
    images = _inventory_images({user_set.set_num, *(fig.fig_num for fig in figures)})
    storage = _storage_by_number(user_set.id)
    figure_images = {}
    for fig in figures:
        for key, image in images[fig.fig_num].items():
            if image:
                figure_images.setdefault(key, image)

    parts = []
    figure_parts = defaultdict(list)
    required = owned = 0
    for is_figure, rows in (
        (False, user_set.parts_in_set),
        (True, user_set.user_minifigure_parts),
    ):
        for row in rows:
            required += row.quantity
            owned += row.have_quantity or 0
            key = row.part_num, row.color_id
            image = row.rebrickable_part.part_img_url if row.rebrickable_part else ""
            if is_figure:
                image = image or figure_images.get(key, image)
                target = figure_parts[row.minifigure_id]
            else:
                image = images[user_set.set_num].get(key) or image
                target = parts
            target.append(_display_part(row, storage.get(row.part_num), image))

    details = {
        "parts": _sort_parts(parts),
        "minifigs": [
            {
                "id": fig.id,
                "fig_num": fig.fig_num,
                "name": fig.rebrickable_minifig.name
                if fig.rebrickable_minifig
                else "Unknown",
                "quantity": fig.quantity,
                "img_url": fig.rebrickable_minifig.img_url
                if fig.rebrickable_minifig
                else "",
                "location": "Not Specified",
                "status": "Not Available",
                "parts": _sort_parts(figure_parts.pop(fig.id, [])),
            }
            for fig in figures
        ],
        "set_img_url": (user_set.template_set and user_set.template_set.img_url)
        or "/static/default_image.png",
        "status": user_set.status,
        "completeness_percentage": completeness_percentage(owned, required),
    }
    if include_unassigned:
        details["unassigned_minifig_parts"] = _sort_parts(
            [part for group in figure_parts.values() for part in group]
        )
    return details


class InvalidSetField(ValueError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def apply_set_edits(user_set, fields, *, legacy=False):
    """Resolve all fields against this copy before assigning. Caller owns the commit."""
    if not legacy and not fields:
        raise InvalidSetField(
            None, "Bitte einen Setstatus oder eine Teilemenge angeben."
        )
    quantities = {}
    if any(field.startswith("part_id_") for field in fields):
        quantities.update({f"part_id_{row.id}": row for row in user_set.parts_in_set})
    if any(field.startswith("minifig_part_id_") for field in fields):
        quantities.update(
            {f"minifig_part_id_{row.id}": row for row in user_set.user_minifigure_parts}
        )
    normalized = {}
    for field, raw in fields.items():
        if field == "status":
            if legacy and not raw:
                continue
            if not isinstance(raw, str) or raw not in USER_SET_STATUSES:
                raise InvalidSetField(field, "Bitte einen gültigen Setstatus wählen.")
            normalized[field] = raw
            continue
        row = quantities.get(field)
        if row is None:
            if legacy:
                continue
            raise InvalidSetField(field, "Dieses Feld gehört nicht zu dieser Setkopie.")
        try:
            value = int(raw) if legacy else parse_integer(raw)
        except ValueError as error:
            raise InvalidSetField(
                field, f"Bitte für {row.part_num} eine ganze Zahl eingeben."
            ) from error
        if not legacy and not 0 <= value <= row.quantity:
            raise InvalidSetField(
                field,
                f"Bitte für {row.part_num} eine Menge zwischen 0 und {row.quantity} eingeben.",
            )
        normalized[field] = max(0, min(value, row.quantity))

    for field, value in normalized.items():
        if field == "status":
            user_set.status = value
        else:
            quantities[field].have_quantity = value
    return {**normalized, "status": user_set.status}
