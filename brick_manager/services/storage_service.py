# pyright: reportCallIssue=false
# Flask-SQLAlchemy generates keyword constructors not visible to static analysis.
"""Physical storage identities, observed arrangements and measured space.

Set ownership stays independent of counted physical contents. All public write
helpers commit once and invalidate the legacy projection after that commit.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from uuid import uuid4

from models import (
    ContainerType,
    LegacyStorageMapping,
    PartStorage,
    RebrickableColors,
    RebrickableInventoryParts,
    RebrickableParts,
    StackRule,
    StorageLocation,
    StorageMove,
    StoragePlacement,
    StorageUnit,
    db,
)
from sqlalchemy import func, or_
from werkzeug.exceptions import BadRequest, Conflict, NotFound


def integer(value, field, minimum=1, optional=False):
    """Reject boolean IDs and numeric strings at the JSON boundary."""
    if optional and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BadRequest(f"{field}: ganze Zahl ab {minimum} erforderlich.")
    return value


def number(value, field, optional=True):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequest(f"{field}: gültiges Maß erforderlich.")
    if (
        not math.isfinite(value)
        or value < 0
        or (
            value == 0
            and field
            in {
                "width_mm",
                "depth_mm",
                "height_mm",
                "height_increment_mm",
                "max_height_mm",
            }
        )
    ):
        raise BadRequest(f"{field}: Maß muss endlich und nicht negativ sein.")
    return value


def text(value, field, optional=False):
    if optional and value is None:
        return None
    if (
        not isinstance(value, str)
        or len(value) > 200
        or (not optional and not value.strip())
    ):
        raise BadRequest(f"{field}: Text mit höchstens 200 Zeichen erforderlich.")
    return value


def choice(value, values, field):
    if not isinstance(value, str) or value not in values:
        raise BadRequest(f"{field}: ungültiger Wert.")
    return value


def boolean(value, field):
    if not isinstance(value, bool):
        raise BadRequest(f"{field}: boolescher Wert erforderlich.")
    return value


def get(model, identifier):
    entity = db.session.get(model, integer(identifier, "id"))
    if entity is None:
        raise NotFound("Lagerobjekt nicht gefunden.")
    return entity


def serialize(entity):
    return {
        column.name: getattr(entity, column.name) for column in entity.__table__.columns
    }


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    from services.part_lookup_service import invalidate_part_lookup_cache

    invalidate_part_lookup_cache()


def check_revision(entity, data):
    if "revision" in data and integer(data["revision"], "revision") != entity.revision:
        raise Conflict("Daten wurden inzwischen geändert. Bitte neu laden.")


def _unreserved(unit_ids=(), storage_ids=()):
    for move in StorageMove.query.filter_by(status="planned").all():
        snapshot = move.snapshot or {}
        if set(map(str, unit_ids)) & set(snapshot.get("units", {})) or set(
            map(str, storage_ids)
        ) & set(snapshot.get("contents", {})):
            raise Conflict("Objekt ist für einen Umräumplan reserviert.")


def _profile(value):
    if value is None:
        return None
    if not isinstance(value, list) or len(value) < 2:
        raise BadRequest("Höhenprofil braucht mindestens zwei Messpunkte.")
    points = []
    for point in value:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise BadRequest("Höhenprofil: [Position, Höhe] erforderlich.")
        points.append([number(point[0], "x", False), number(point[1], "height", False)])
    if any(points[i][0] >= points[i + 1][0] for i in range(len(points) - 1)):
        raise BadRequest("Messpunkte müssen von links nach rechts geordnet sein.")
    return points


def create_location(data):
    kind = choice(data.get("kind"), {"zone", "rack", "shelf", "unresolved"}, "kind")
    parent_id = integer(data.get("parent_id"), "parent_id", optional=True)
    if parent_id:
        parent = get(StorageLocation, parent_id)
        if (kind, parent.kind) not in {
            ("rack", "zone"),
            ("shelf", "rack"),
            ("unresolved", "zone"),
        }:
            raise BadRequest("Ungültige Ortshierarchie.")
    elif kind not in {"zone", "unresolved"}:
        raise BadRequest("Regal und Fach benötigen einen übergeordneten Ort.")
    location = StorageLocation(
        kind=kind,
        parent_id=parent_id,
        label=text(data.get("label"), "label"),
        sort_order=integer(data.get("sort_order", 0), "sort_order", 0),
    )
    db.session.add(location)
    _location_fields(location, data)
    commit()
    return serialize(location)


def _location_fields(location, data):
    for field in ("width_mm", "depth_mm"):
        if field in data:
            setattr(location, field, number(data[field], field))
    if "height_profile" in data:
        location.height_profile = _profile(data["height_profile"])
    if "zone_kind" in data:
        location.zone_kind = choice(
            data["zone_kind"], {"active", "archive"}, "zone_kind"
        )
    if "measurement_status" in data:
        location.measurement_status = choice(
            data["measurement_status"],
            {"unknown", "measured", "confirmed"},
            "measurement_status",
        )
        location.measured_at = (
            datetime.now(UTC).replace(tzinfo=None)
            if location.measurement_status != "unknown"
            else None
        )


def update_location(identifier, data):
    location = get(StorageLocation, identifier)
    check_revision(location, data)
    _unreserved(
        unit_ids=[
            p.unit_id
            for p in StoragePlacement.query.filter_by(shelf_id=identifier).all()
        ]
    )
    if "label" in data:
        location.label = text(data["label"], "label")
    _location_fields(location, data)
    location.revision += 1
    commit()
    return serialize(location)


def _type_fields(entity, data):
    for field in ("width_mm", "depth_mm", "height_mm"):
        if field in data:
            setattr(entity, field, number(data[field], field))
    if "access_mode" in data:
        entity.access_mode = choice(
            data["access_mode"],
            {"front_open", "remove_above", "drawer", "unknown"},
            "access_mode",
        )
    if "dimensions_status" in data:
        entity.dimensions_status = choice(
            data["dimensions_status"],
            {
                "unknown",
                "auftrag",
                "produktangabe",
                "gemessen",
                "vor_ort_bestaetigt",
                "measured",
                "confirmed",
            },
            "dimensions_status",
        )
    if "drawer_count" in data:
        entity.drawer_count = integer(
            data["drawer_count"], "drawer_count", optional=True
        )
    if "properties" in data:
        if not isinstance(data["properties"], dict):
            raise BadRequest("properties muss ein Objekt sein.")
        entity.properties = data["properties"]


def create_type(data):
    name = text(data.get("name"), "name")
    if ContainerType.query.filter_by(name=name).first():
        raise Conflict("Behältertyp existiert bereits.")
    entity = ContainerType(
        name=name,
        kind=choice(
            data.get("kind", "container"),
            {"container", "cabinet", "drawer", "compartment"},
            "kind",
        ),
    )
    _type_fields(entity, data)
    db.session.add(entity)
    commit()
    return serialize(entity)


def update_type(identifier, data):
    entity = get(ContainerType, identifier)
    _unreserved(
        unit_ids=[u.id for u in StorageUnit.query.filter_by(type_id=identifier).all()]
    )
    _type_fields(entity, data)
    # Units referencing this type participate in optimistic move validation.
    for unit in StorageUnit.query.filter_by(type_id=identifier).all():
        unit.revision += 1
    commit()
    return serialize(entity)


def seed_container_types():
    """Explicit setup action; source dimensions stay unmeasured until checked."""
    definitions = [
        ("HMH XS", 90, 102, 50, "front_open", None),
        ("HMH S", 161, 105, 75, "front_open", None),
        ("HMH 3", 248, 145, 127, "front_open", None),
        ("Feinkost 125 ml", None, None, None, "remove_above", None),
        ("Feinkost 250 ml", None, None, None, "remove_above", None),
        ("Feinkost 500 ml", None, None, None, "remove_above", None),
        ("CYEER 750 ml", None, None, None, "remove_above", None),
        ("STANLEY 1-93-980", None, None, None, "drawer", 30),
        ("STANLEY 1-93-978", None, None, None, "drawer", 9),
    ]
    for name, width, depth, height, access, drawers in definitions:
        if not ContainerType.query.filter_by(name=name).first():
            db.session.add(
                ContainerType(
                    name=name,
                    kind="cabinet" if drawers else "container",
                    width_mm=width,
                    depth_mm=depth,
                    height_mm=height,
                    access_mode=access,
                    drawer_count=drawers,
                    dimensions_status="auftrag" if width else "unknown",
                    properties={"same_size_only": True, "stack_group": name}
                    if name.startswith("HMH")
                    else {},
                )
            )
    commit()
    return [serialize(t) for t in ContainerType.query.order_by(ContainerType.id).all()]


def create_unit(data):
    entity_type = (
        get(ContainerType, data.get("type_id"))
        if data.get("type_id") is not None
        else None
    )
    kind = choice(
        data.get("kind", entity_type.kind if entity_type else "container"),
        {"container", "cabinet", "drawer", "compartment"},
        "kind",
    )
    if kind in {"drawer", "compartment"}:
        raise BadRequest(
            "Schubladen und Unterteilungen werden über ihr Magazin angelegt."
        )
    unit = StorageUnit(
        type_id=entity_type.id if entity_type else None,
        kind=kind,
        label=text(data.get("label"), "label"),
        contents_complete=boolean(
            data.get("contents_complete", False), "contents_complete"
        ),
        fill_state=choice(
            data.get("fill_state", "unknown"),
            {"unknown", "space", "nearly_full", "full"},
            "fill_state",
        ),
    )
    db.session.add(unit)
    db.session.flush()
    if kind == "cabinet" and entity_type and entity_type.drawer_count:
        for index in range(1, entity_type.drawer_count + 1):
            db.session.add(
                StorageUnit(
                    kind="drawer",
                    label=str(index),
                    ordinal=index,
                    host_unit_id=unit.id,
                    partition_count=1,
                    fill_state="unknown",
                    contents_complete=False,
                )
            )
    commit()
    return unit_details(unit.id)


def update_unit(identifier, data):
    unit = get(StorageUnit, identifier)
    check_revision(unit, data)
    _unreserved(unit_ids=[identifier])
    for field in ("label",):
        if field in data:
            setattr(unit, field, text(data[field], field))
    if "fill_state" in data:
        unit.fill_state = choice(
            data["fill_state"],
            {"unknown", "space", "nearly_full", "full"},
            "fill_state",
        )
    for field in ("contents_complete", "label_printed"):
        if field in data:
            setattr(unit, field, boolean(data[field], field))
    if "active" in data:
        active = boolean(data["active"], "active")
        if not active and (
            PartStorage.query.filter_by(storage_unit_id=identifier).first()
            or StoragePlacement.query.filter_by(support_unit_id=identifier).first()
            or db.session.get(StoragePlacement, identifier)
        ):
            raise Conflict(
                "Belegte oder aufgestellte Einheit kann nicht stillgelegt werden."
            )
        unit.active = active
    unit.revision += 1
    commit()
    return unit_details(identifier)


def partition_drawer(identifier, data):
    drawer = get(StorageUnit, identifier)
    if drawer.kind != "drawer":
        raise BadRequest("Nur Schubladen können unterteilt werden.")
    check_revision(drawer, data)
    _unreserved(unit_ids=[identifier])
    count = integer(data.get("partition_count"), "partition_count")
    if count not in {1, 2, 3}:
        raise BadRequest("Eine, zwei oder drei Unterteilungen möglich.")
    if count == drawer.partition_count:
        return unit_details(identifier)
    children = StorageUnit.query.filter_by(host_unit_id=identifier, active=True).all()
    occupied = [identifier] + [u.id for u in children]
    if (
        count != drawer.partition_count
        and PartStorage.query.filter(
            PartStorage.storage_unit_id.in_(occupied),
            (PartStorage.quantity.is_(None)) | (PartStorage.quantity > 0),
        ).first()
    ):
        raise Conflict("Inhalt zuerst bestätigt in eine Zwischenablage umbuchen.")
    for child in children:
        child.active = False
    if count > 1:
        for index in range(count):
            db.session.add(
                StorageUnit(
                    kind="compartment",
                    label=chr(65 + index),
                    host_unit_id=identifier,
                    ordinal=index + 1,
                    fill_state="unknown",
                    contents_complete=False,
                )
            )
    drawer.partition_count = count
    drawer.revision += 1
    commit()
    return unit_details(identifier)


def _placement_data(unit_id, data):
    unit = get(StorageUnit, unit_id)
    if (
        unit.host_unit_id
        or unit.kind not in {"container", "cabinet"}
        or not unit.active
    ):
        raise BadRequest("Diese Einheit kann nicht frei aufgestellt werden.")
    shelf_id = integer(data.get("shelf_id"), "shelf_id", optional=True)
    support_id = integer(data.get("support_unit_id"), "support_unit_id", optional=True)
    if bool(shelf_id) == bool(support_id):
        raise BadRequest("Genau ein Fach oder eine Unterlage erforderlich.")
    relation = choice(
        data.get("relation_kind", "stacked" if support_id else "on_shelf"),
        {"on_shelf", "stacked", "loose_on"},
        "relation_kind",
    )
    if shelf_id:
        if get(StorageLocation, shelf_id).kind != "shelf" or relation != "on_shelf":
            raise BadRequest("Aufstellung benötigt ein Fach und on_shelf.")
    else:
        support = get(StorageUnit, support_id)
        if (
            support.kind not in {"container", "cabinet"}
            or not support.active
            or relation == "on_shelf"
        ):
            raise BadRequest("Ungültige Auflage.")
        seen = {unit_id}
        cursor = support_id
        while cursor is not None:
            if cursor in seen:
                raise Conflict("Auflage würde einen Zyklus erzeugen.")
            seen.add(cursor)
            placement = db.session.get(StoragePlacement, cursor)
            cursor = placement.support_unit_id if placement else None
        lower = (
            db.session.get(ContainerType, support.type_id) if support.type_id else None
        )
        upper = db.session.get(ContainerType, unit.type_id) if unit.type_id else None
        if relation == "stacked" and lower and upper:
            if (
                lower.name.startswith("HMH") or upper.name.startswith("HMH")
            ) and lower.name != upper.name:
                raise Conflict("Sichtlagerboxen nur innerhalb derselben Größe stapeln.")
            lower_group = (lower.properties or {}).get("stack_group")
            upper_group = (upper.properties or {}).get("stack_group")
            if (
                (lower.properties or {}).get("same_size_only")
                or (upper.properties or {}).get("same_size_only")
            ) and (not lower_group or lower_group != upper_group):
                raise Conflict("Sichtlagerboxen nur innerhalb derselben Größe stapeln.")
        if support.type_id is None or unit.type_id is None:
            rule = None
        else:
            rule = StackRule.query.filter_by(
                lower_type_id=support.type_id,
                upper_type_id=unit.type_id,
                relation_kind=relation,
                verified=True,
            ).first()
        if rule is None and not data.get("observed_unverified", False):
            raise Conflict(
                "Diese Stapel-/Auflagekombination ist noch nicht verifiziert."
            )
        if (
            relation == "stacked"
            and StoragePlacement.query.filter_by(
                support_unit_id=support_id, relation_kind="stacked"
            )
            .filter(StoragePlacement.unit_id != unit_id)
            .first()
        ):
            raise Conflict("Stapelposition ist bereits belegt.")
    return {
        "shelf_id": shelf_id,
        "support_unit_id": support_id,
        "relation_kind": relation,
        "order_left": integer(data.get("order_left", 0), "order_left", 0),
        "x_mm": number(data.get("x_mm"), "x_mm"),
        "depth_offset_mm": number(data.get("depth_offset_mm"), "depth_offset_mm"),
        "orientation": choice(
            data.get("orientation", "normal"), {"normal", "rotated"}, "orientation"
        ),
    }


def place_unit(identifier, data, initial_only=True):
    if db.session.get(StoragePlacement, identifier) is not None:
        raise Conflict(
            "Aufgestellte Behälter nur über bestätigte Bewegung verschieben."
        )
    values = _placement_data(identifier, data)
    preview = preview_placement(identifier, data)
    if preview["status"] == "no_fit":
        raise Conflict("Aufstellung passt nicht: " + "; ".join(preview["reasons"]))
    _unreserved(
        unit_ids=[identifier]
        + ([values["support_unit_id"]] if values["support_unit_id"] else [])
    )
    db.session.add(StoragePlacement(unit_id=identifier, **values))
    unit = get(StorageUnit, identifier)
    unit.revision += 1
    commit()
    return unit_details(identifier)


def save_stack_rule(data):
    lower = get(ContainerType, data.get("lower_type_id"))
    upper = get(ContainerType, data.get("upper_type_id"))
    relation = choice(
        data.get("relation_kind", "stacked"), {"stacked", "loose_on"}, "relation_kind"
    )
    if (
        relation == "stacked"
        and (lower.name.startswith("HMH") or upper.name.startswith("HMH"))
        and lower.name != upper.name
    ):
        raise Conflict("Sichtlagerboxen unterschiedlicher Größe nicht stapeln.")
    if relation == "stacked" and lower.name.startswith("CYEER"):
        raise Conflict("CYEER-Auflage als lose Auflage erfassen.")
    _unreserved(
        unit_ids=[
            unit.id
            for unit in StorageUnit.query.filter(
                StorageUnit.type_id.in_([lower.id, upper.id])
            ).all()
        ]
    )
    if (
        relation == "stacked"
        and (
            (lower.properties or {}).get("same_size_only")
            or (upper.properties or {}).get("same_size_only")
        )
        and lower.id != upper.id
    ):
        raise Conflict("Sichtlagerboxen unterschiedlicher Größe nicht stapeln.")
    rule = (
        get(StackRule, data["id"])
        if data.get("id")
        else StackRule.query.filter_by(
            lower_type_id=lower.id, upper_type_id=upper.id, relation_kind=relation
        ).first()
    )
    if rule is None:
        rule = StackRule(
            lower_type_id=lower.id, upper_type_id=upper.id, relation_kind=relation
        )
        db.session.add(rule)
    rule.verified = boolean(data.get("verified", False), "verified")
    rule.source = text(data.get("source", "vor_ort_bestaetigt"), "source")
    rule.verified_at = datetime.now(UTC).replace(tzinfo=None) if rule.verified else None
    rule.height_increment_mm = number(
        data.get("height_increment_mm"), "height_increment_mm"
    )
    rule.max_count = integer(data.get("max_count"), "max_count", optional=True)
    rule.max_height_mm = number(data.get("max_height_mm"), "max_height_mm")
    commit()
    return serialize(rule)


def location_path(identifier):
    result = []
    seen = set()
    while identifier is not None:
        if identifier in seen:
            raise Conflict("Zyklus in Lagerorten.")
        seen.add(identifier)
        loc = get(StorageLocation, identifier)
        result.append(serialize(loc))
        identifier = loc.parent_id
    return list(reversed(result))


def unit_address(identifier):
    seen = set()
    chain = []
    shelf_id = None
    while identifier is not None:
        if identifier in seen:
            raise Conflict("Zyklus in Aufstellung.")
        seen.add(identifier)
        unit = get(StorageUnit, identifier)
        chain.append({"id": unit.id, "label": unit.label, "kind": unit.kind})
        if unit.host_unit_id:
            identifier = unit.host_unit_id
        else:
            placement = db.session.get(StoragePlacement, identifier)
            if not placement:
                break
            if placement.shelf_id:
                shelf_id = placement.shelf_id
                break
            identifier = placement.support_unit_id
    path = location_path(shelf_id) if shelf_id else []
    return {
        "shelf_id": shelf_id,
        "location_path": path,
        "unit_path": list(reversed(chain)),
        "known": bool(shelf_id),
        "display": " / ".join(
            [str(p["label"]) for p in path] + [str(u["label"]) for u in reversed(chain)]
        )
        or "Fundort ungeklärt",
    }


def catalog_images(part_nums):
    """Batch inventory-image fallback; exact color first, then any known image."""
    if not part_nums:
        return {}
    rows = (
        db.session.query(
            RebrickableInventoryParts.part_num,
            RebrickableInventoryParts.color_id,
            func.min(RebrickableInventoryParts.img_url),
        )
        .filter(
            RebrickableInventoryParts.part_num.in_(part_nums),
            RebrickableInventoryParts.img_url.isnot(None),
            func.trim(RebrickableInventoryParts.img_url).notin_(["", "None"]),
        )
        .group_by(
            RebrickableInventoryParts.part_num, RebrickableInventoryParts.color_id
        )
        .order_by(
            RebrickableInventoryParts.part_num, RebrickableInventoryParts.color_id
        )
        .all()
    )
    images = {}
    for part_num, color_id, url in rows:
        images[(part_num, color_id)] = url
        images.setdefault(part_num, url)
    return images


def content_dict(content, images=None):
    result = serialize(content)
    part = content.rebrickable_part
    color = content.rebrickable_color
    result["part_name"] = part.name if part else "Katalogdaten fehlen"
    images = images or {}
    result["part_img_url"] = (
        (
            images.get((content.part_num, content.color_id))
            if content.color_id is not None
            else None
        )
        or (
            part.part_img_url
            if part and part.part_img_url not in {"", "None"}
            else None
        )
        or images.get(content.part_num)
    )
    result["color_name"] = color.name if color else None
    result["color_rgb"] = color.rgb if color else None
    if content.storage_unit_id:
        address = unit_address(content.storage_unit_id)
        by_kind = {p["kind"]: p["label"] for p in address["location_path"]}
        result.update(
            location=by_kind.get("rack"),
            level=by_kind.get("shelf"),
            box=get(StorageUnit, content.storage_unit_id).label,
        )
        result["address"] = address
        result["warehouse_url"] = f"/warehouse?unit_id={content.storage_unit_id}"
    else:
        result["address"] = {
            "known": False,
            "display": " / ".join(
                str(x) for x in (content.location, content.level, content.box) if x
            )
            or "Fundort ungeklärt",
        }
        result["warehouse_url"] = "/warehouse"
    return result


def list_part_locations(part_num, color_id=None):
    query = PartStorage.query.filter_by(part_num=part_num)
    if color_id is not None:
        query = query.filter_by(color_id=color_id)
    rows = [content_dict(c) for c in query.order_by(PartStorage.id).all()]
    plans = StorageMove.query.filter_by(status="planned").order_by(StorageMove.id).all()
    for row in rows:
        row["planned_moves"] = []
        address_units = {unit["id"] for unit in row["address"].get("unit_path", [])}
        for plan in plans:
            for item in (plan.payload or {}).get("items", []):
                if (
                    item.get("storage_id") != row["id"]
                    and item.get("unit_id") not in address_units
                ):
                    continue
                target_id = item.get("target_unit_id")
                target = item.get("target_placement", {})
                if target_id:
                    display = unit_address(target_id)["display"]
                elif target.get("shelf_id"):
                    display = " / ".join(
                        str(loc["label"]) for loc in location_path(target["shelf_id"])
                    )
                elif target.get("support_unit_id"):
                    display = (
                        unit_address(target["support_unit_id"])["display"]
                        + " / obere Auflage"
                    )
                else:
                    display = "Leere Einheit aus Aufstellung nehmen"
                row["planned_moves"].append(
                    {
                        "id": plan.id,
                        "quantity": item.get("quantity"),
                        "destination": display,
                        "status": "planned",
                    }
                )
    return rows


def _content_target(unit_id):
    unit = get(StorageUnit, unit_id)
    if (
        not unit.active
        or unit.kind == "cabinet"
        or (unit.kind == "drawer" and unit.partition_count != 1)
    ):
        raise BadRequest(
            "Inhalt benötigt aktiven Behälter oder adressierbare Unterteilung."
        )
    return unit


def save_content(data):
    unit = _content_target(data.get("storage_unit_id"))
    _unreserved(unit_ids=[unit.id])
    part_num = text(data.get("part_num"), "part_num")
    if db.session.get(RebrickableParts, part_num) is None:
        raise NotFound("Bricks-Teilenummer nicht im Katalog.")
    color_id = integer(data.get("color_id"), "color_id", minimum=0, optional=True)
    if color_id is not None and db.session.get(RebrickableColors, color_id) is None:
        raise NotFound("Farbe nicht gefunden.")
    quantity = integer(data.get("quantity"), "quantity", 0, optional=True)
    if quantity is not None:
        raise Conflict(
            "Gezählten Zugang bitte über einen bestätigten Aufnahmeauftrag buchen."
        )
    entry = PartStorage(
        part_num=part_num,
        color_id=color_id,
        storage_unit_id=unit.id,
        quantity=None,
        notes=text(data.get("notes"), "notes", True),
        migration_status="confirmed",
    )
    db.session.add(entry)
    unit.contents_complete = False
    unit.revision += 1
    commit()
    return content_dict(entry)


def update_content(identifier, data):
    entry = get(PartStorage, identifier)
    check_revision(entry, data)
    _unreserved(
        storage_ids=[entry.id],
        unit_ids=[entry.storage_unit_id] if entry.storage_unit_id else [],
    )
    old_quantity = entry.quantity
    old_color = entry.color_id
    new_color = entry.color_id
    if "color_id" in data:
        new_color = integer(data["color_id"], "color_id", 0, optional=True)
        if (
            new_color is not None
            and db.session.get(RebrickableColors, new_color) is None
        ):
            raise NotFound("Farbe nicht gefunden.")
        if old_color is not None and new_color != old_color:
            raise Conflict(
                "Bekannte Teil-/Farbidentität nicht überschreiben. Korrektur getrennt klären."
            )
    needs_audit = "quantity" in data or new_color != old_color
    reason = text(data.get("reason"), "reason") if needs_audit else None
    new_quantity = (
        integer(data["quantity"], "quantity", 0, optional=True)
        if "quantity" in data
        else old_quantity
    )
    if "storage_unit_id" in data:
        target = _content_target(data["storage_unit_id"])
        _unreserved(unit_ids=[target.id])
        if entry.storage_unit_id and entry.storage_unit_id != target.id:
            raise Conflict("Fundortwechsel benötigt bestätigte Bewegung.")
        entry.storage_unit_id = target.id
        entry.migration_status = "confirmed"
    entry.color_id = new_color
    entry.quantity = new_quantity
    if needs_audit:
        db.session.add(
            StorageMove(
                kind="count",
                status="confirmed",
                reason=reason,
                payload={"storage_id": entry.id},
                snapshot={
                    "quantity_before": old_quantity,
                    "quantity_after": entry.quantity,
                    **(
                        {"color_before": old_color, "color_after": entry.color_id}
                        if old_color != entry.color_id
                        else {}
                    ),
                },
                confirmed_at=datetime.now(UTC).replace(tzinfo=None),
                idempotency_key=f"count-{uuid4().hex}",
            )
        )
    if "notes" in data:
        entry.notes = text(data["notes"], "notes", True)
    entry.revision += 1
    if entry.storage_unit_id:
        unit = get(StorageUnit, entry.storage_unit_id)
        unit.revision += 1
        unit.label_printed = False
        mapping = db.session.get(LegacyStorageMapping, entry.id)
        if mapping:
            mapping.storage_unit_id = entry.storage_unit_id
            mapping.confirmed = True
    commit()
    return content_dict(entry)


def unit_details(identifier):
    unit = get(StorageUnit, identifier)
    result = serialize(unit)
    result["address"] = unit_address(identifier)
    placement = db.session.get(StoragePlacement, identifier)
    result["placement"] = serialize(placement) if placement else None
    result["contents"] = [
        content_dict(c)
        for c in PartStorage.query.filter_by(storage_unit_id=identifier)
        .order_by(PartStorage.id)
        .all()
    ]
    result["children"] = [
        serialize(u)
        for u in StorageUnit.query.filter_by(host_unit_id=identifier, active=True)
        .order_by(StorageUnit.ordinal)
        .all()
    ]
    result["above"] = [
        p.unit_id
        for p in StoragePlacement.query.filter_by(support_unit_id=identifier).all()
    ]
    ctype = db.session.get(ContainerType, unit.type_id) if unit.type_id else None
    result["access_mode"] = ctype.access_mode if ctype else "unknown"
    result["access_requires_removal"] = (
        result["above"] if result["access_mode"] != "front_open" else []
    )
    result["empty"] = bool(unit.contents_complete) and all(
        c["quantity"] == 0 for c in result["contents"]
    )
    return result


def _dimensions(unit):
    ctype = db.session.get(ContainerType, unit.type_id) if unit.type_id else None
    if ctype is None:
        return None, None, None, False
    props = unit.properties or {}
    return (
        props.get("width_mm", ctype.width_mm),
        props.get("depth_mm", ctype.depth_mm),
        props.get("height_mm", ctype.height_mm),
        ctype.dimensions_status
        in {"gemessen", "vor_ort_bestaetigt", "measured", "confirmed"},
    )


def _height_at(profile, x):
    for (x1, h1), (x2, h2) in zip(profile, profile[1:], strict=False):
        if x1 <= x <= x2:
            return h1 + (h2 - h1) * (x - x1) / (x2 - x1)
    return None


def _subtree_height(identifier, seen=None):
    """Return measured envelope height and all reasons preventing a fit claim."""
    seen = set() if seen is None else set(seen)
    if identifier in seen:
        raise Conflict("Zyklus in Aufstellung.")
    seen.add(identifier)
    unit = get(StorageUnit, identifier)
    _width, _depth, height, measured = _dimensions(unit)
    reasons = [] if measured else ["Behältermaße/Orientierung noch nicht gemessen."]
    maximum = height
    depth = 1
    for child_placement in StoragePlacement.query.filter_by(
        support_unit_id=identifier
    ).all():
        child = get(StorageUnit, child_placement.unit_id)
        child_height, child_depth, missing = _subtree_height(child.id, seen)
        reasons.extend(missing)
        rule = StackRule.query.filter_by(
            lower_type_id=unit.type_id,
            upper_type_id=child.type_id,
            relation_kind=child_placement.relation_kind,
            verified=True,
        ).first()
        _cw, _cd, own_height, _cv = _dimensions(child)
        if (
            rule
            and rule.height_increment_mm is not None
            and None not in (height, own_height, child_height)
        ):
            branch = height + rule.height_increment_mm + child_height - own_height
            if rule.max_count and child_depth + 1 > rule.max_count:
                raise Conflict("Bestätigte maximale Stapelzahl überschritten.")
            if rule.max_height_mm is not None and branch > rule.max_height_mm:
                raise Conflict("Bestätigte maximale Stapelhöhe überschritten.")
            maximum = max(maximum, branch) if maximum is not None else None
        else:
            maximum = None
            reasons.append("Stapelhöhenzunahme oder Kombination ungeprüft.")
        depth = max(depth, child_depth + 1)
    return maximum, depth, reasons


def preview_placement(identifier, data):
    """Three-valued fit result for the entire supported envelope."""
    values = _placement_data(identifier, data)
    unit = get(StorageUnit, identifier)
    width, depth, own_height, verified = _dimensions(unit)
    height, stack_depth, reasons = _subtree_height(identifier)
    if values["orientation"] == "rotated":
        width, depth = depth, width
    shelf_id = values["shelf_id"]
    legacy_rows = 0
    x, y = values["x_mm"], values["depth_offset_mm"]
    current = unit
    edge = values
    seen = {identifier}
    while edge.get("support_unit_id"):
        support = get(StorageUnit, edge["support_unit_id"])
        if support.id in seen:
            raise Conflict("Zyklus in Aufstellung.")
        seen.add(support.id)
        support_placement = db.session.get(StoragePlacement, support.id)
        sw, sd, sh, sm = _dimensions(support)
        if support_placement and support_placement.orientation == "rotated":
            sw, sd = sd, sw
        if not sm:
            reasons.append("Unterlagenmaße ungeprüft.")
        # Offsets on a support are relative to its upper surface, not to the shelf.
        local_x = edge.get("x_mm")
        local_y = edge.get("depth_offset_mm")
        if edge["relation_kind"] == "stacked":
            local_x = 0 if local_x is None else local_x
            local_y = 0 if local_y is None else local_y
        cw, cd, ch, _cm = _dimensions(current)
        if edge.get("orientation", "normal") == "rotated":
            cw, cd = cd, cw
        if cw is not None and cd is not None and sw is not None and sd is not None:
            if (
                cw > sw
                or cd > sd
                or (local_x is not None and local_x + cw > sw)
                or (local_y is not None and local_y + cd > sd)
            ):
                return {
                    "status": "no_fit",
                    "reasons": ["Auflagefläche oder Auflageposition zu klein."],
                }
        else:
            reasons.append("Auflagefläche ungemessen.")
        if local_x is None or local_y is None:
            reasons.append("Position auf loser Auflage ungemessen.")
        for sibling_edge in StoragePlacement.query.filter_by(
            support_unit_id=support.id
        ).all():
            if sibling_edge.unit_id == current.id:
                continue
            sibling = get(StorageUnit, sibling_edge.unit_id)
            sibling_width, sibling_depth, _sibling_height, sibling_measured = (
                _dimensions(sibling)
            )
            if sibling_edge.orientation == "rotated":
                sibling_width, sibling_depth = sibling_depth, sibling_width
            sx, sy = sibling_edge.x_mm, sibling_edge.depth_offset_mm
            if sibling_edge.relation_kind == "stacked":
                sx = 0 if sx is None else sx
                sy = 0 if sy is None else sy
            if (
                local_x is None
                or local_y is None
                or cw is None
                or cd is None
                or sx is None
                or sy is None
                or sibling_width is None
                or sibling_depth is None
                or not sibling_measured
            ):
                reasons.append("Benachbarte Auflageposition oder Maße ungeprüft.")
            elif (
                local_x < sx + sibling_width
                and sx < local_x + cw
                and local_y < sy + sibling_depth
                and sy < local_y + cd
            ):
                return {
                    "status": "no_fit",
                    "reasons": ["Auflagefläche bereits belegt."],
                }
        rule = StackRule.query.filter_by(
            lower_type_id=support.type_id,
            upper_type_id=current.type_id,
            relation_kind=edge["relation_kind"],
            verified=True,
        ).first()
        if (
            rule
            and rule.height_increment_mm is not None
            and None not in (height, ch, sh)
        ):
            height = sh + rule.height_increment_mm + height - ch
            stack_depth += 1
            if (rule.max_count and stack_depth > rule.max_count) or (
                rule.max_height_mm is not None and height > rule.max_height_mm
            ):
                return {
                    "status": "no_fit",
                    "reasons": ["Bestätigte Stapelgrenze überschritten."],
                }
        else:
            height = None
            reasons.append("Stapelhöhenzunahme oder Kombination ungeprüft.")
        if support_placement is None:
            shelf_id = None
            break
        px = support_placement.x_mm
        py = support_placement.depth_offset_mm
        if support_placement.relation_kind == "stacked":
            px = 0 if px is None else px
            py = 0 if py is None else py
        x = local_x + px if local_x is not None and px is not None else None
        y = local_y + py if local_y is not None and py is not None else None
        if support_placement.shelf_id:
            shelf_id = support_placement.shelf_id
            break
        # Carry accumulated offsets upward while following the next lower edge.
        edge = serialize(support_placement)
        edge["x_mm"], edge["depth_offset_mm"] = x, y
        current = support
    if not verified:
        reasons.append("Behältermaße/Orientierung noch nicht gemessen.")
    if not shelf_id:
        reasons.append("Fachzuordnung ungeklärt.")
    else:
        shelf = get(StorageLocation, shelf_id)
        legacy_rows = _legacy_rows_for_shelf(shelf)
        if legacy_rows:
            reasons.append(
                "Vorhandene Lagerzuordnungen sind noch nicht als physische Behälter verortet."
            )
        if (
            shelf.width_mm is None
            or shelf.depth_mm is None
            or width is None
            or depth is None
            or height is None
            or x is None
            or y is None
            or not shelf.height_profile
        ):
            reasons.append("Fachmaße, Position, Tiefe oder Höhenprofil fehlen.")
        else:
            if x + width > shelf.width_mm or y + depth > shelf.depth_mm:
                return {
                    "status": "no_fit",
                    "reasons": ["Fachbreite oder Tiefe überschritten."],
                }
            points = [x, x + width] + [
                p[0] for p in shelf.height_profile if x < p[0] < x + width
            ]
            available = [_height_at(shelf.height_profile, px) for px in points]
            if any(h is None for h in available):
                reasons.append("Höhenprofil deckt die Standfläche nicht ab.")
            elif min(h for h in available if h is not None) < height:
                return {
                    "status": "no_fit",
                    "reasons": ["Stapel kollidiert mit Dachschräge/Fachhöhe."],
                }
            if shelf.measurement_status not in {"measured", "confirmed"}:
                reasons.append("Fachmessung ungeprüft.")
            if not values["support_unit_id"]:
                for placement in StoragePlacement.query.filter_by(
                    shelf_id=shelf_id
                ).all():
                    if placement.unit_id == identifier:
                        continue
                    ow, od, _oh, ov = _dimensions(get(StorageUnit, placement.unit_id))
                    if placement.orientation == "rotated":
                        ow, od = od, ow
                    if (
                        placement.x_mm is None
                        or ow is None
                        or od is None
                        or placement.depth_offset_mm is None
                        or not ov
                    ):
                        reasons.append("Nachbarposition oder Nachbarmaße fehlen.")
                    elif (
                        x < placement.x_mm + ow
                        and placement.x_mm < x + width
                        and y < placement.depth_offset_mm + od
                        and placement.depth_offset_mm < y + depth
                    ):
                        return {
                            "status": "no_fit",
                            "reasons": ["Stellfläche ist bereits belegt."],
                        }
    if values["support_unit_id"]:
        reasons.append("Lastgrenze und Entnahmefreiraum vor Ort prüfen.")
    return {
        "status": "unknown" if reasons else "fits",
        "reasons": sorted(set(reasons)),
        "legacy_rows": legacy_rows,
    }


def _legacy_rows_for_shelf(shelf):
    """Known legacy occupancy cannot be interpreted as empty floor space."""
    if shelf.kind != "shelf" or shelf.parent_id is None:
        return 0
    rack = db.session.get(StorageLocation, shelf.parent_id)
    if rack is None or rack.kind != "rack":
        return 0
    return PartStorage.query.filter(
        PartStorage.storage_unit_id.is_(None),
        PartStorage.location == rack.label,
        or_(
            PartStorage.level == shelf.label,
            PartStorage.level.is_(None),
            func.trim(PartStorage.level) == "",
        ),
    ).count()


def space_report(shelf_id):
    shelf = get(StorageLocation, shelf_id)
    legacy_rows = _legacy_rows_for_shelf(shelf)
    bases = (
        StoragePlacement.query.filter_by(shelf_id=shelf_id)
        .order_by(StoragePlacement.order_left)
        .all()
    )
    intervals = []
    unknown = bool(legacy_rows)
    for placement in bases:
        width, depth, _height, verified = _dimensions(
            get(StorageUnit, placement.unit_id)
        )
        if placement.orientation == "rotated":
            width, depth = depth, width
        if (
            placement.x_mm is None
            or placement.depth_offset_mm is None
            or width is None
            or depth is None
            or _height is None
            or not verified
        ):
            unknown = True
        else:
            intervals.append([placement.x_mm, placement.x_mm + width])
    free = []
    if (
        shelf.width_mm is not None
        and not unknown
        and shelf.measurement_status in {"measured", "confirmed"}
    ):
        cursor = 0
        for left, right in sorted(intervals):
            if left > cursor:
                free.append([cursor, left])
            cursor = max(cursor, right)
        if cursor < shelf.width_mm:
            free.append([cursor, shelf.width_mm])
    return {
        "shelf_id": shelf_id,
        "base_count": len(bases),
        "legacy_rows": legacy_rows,
        "legacy_occupancy_unknown": bool(legacy_rows),
        "free_intervals_mm": free,
        "fit_known": not unknown
        and shelf.width_mm is not None
        and shelf.depth_mm is not None
        and bool(shelf.height_profile)
        and shelf.measurement_status in {"measured", "confirmed"},
        "note": "Leere Behälter belegen weiterhin Stellfläche. Niedrigere Stapel geben nicht automatisch Grundfläche frei. Getrennte Lücken bleiben getrennt.",
    }


def legacy_storage_groups(locations, contents):
    """Project original label groups, never create or assert physical identity."""
    location_by_id = {row["id"]: row for row in locations}
    shelves_by_label = {}
    for shelf in locations:
        if shelf["kind"] != "shelf":
            continue
        rack = location_by_id.get(shelf["parent_id"])
        if rack and rack["kind"] == "rack":
            shelves_by_label.setdefault((rack["label"], shelf["label"]), []).append(
                shelf["id"]
            )
    groups = {}
    for row in contents:
        if row["storage_unit_id"] is not None:
            continue
        address = (row["location"], row["level"], row["box"])
        key = json.dumps(address, ensure_ascii=False, separators=(",", ":"))
        if key not in groups:
            candidates = shelves_by_label.get(address[:2], [])
            groups[key] = {
                "key": key,
                "shelf_id": candidates[0] if len(candidates) == 1 else None,
                "shelf_candidates": list(candidates),
                "location": address[0],
                "level": address[1],
                "box": address[2],
                "storage_ids": [],
                "contents": [],
                "physical_verified": False,
            }
        groups[key]["storage_ids"].append(row["id"])
        groups[key]["contents"].append(row)
    for group in groups.values():
        group["row_count"] = len(group["storage_ids"])
        group["variant_count"] = len(
            {(row["part_num"], row["color_id"]) for row in group["contents"]}
        )
    return list(groups.values())


def _overview_locations():
    return [
        serialize(row)
        for row in StorageLocation.query.order_by(
            StorageLocation.sort_order, StorageLocation.id
        ).all()
    ]


def _natural_label(value):
    return [
        (0, int(piece)) if piece.isdigit() else (1, piece.casefold())
        for piece in re.split(r"(\d+)", value)
    ]


def legacy_group_contents(storage_id):
    row = get(PartStorage, storage_id)
    if row.storage_unit_id is not None:
        raise Conflict("Inhalt ist bereits einem Behälter zugeordnet.")
    rows = (
        PartStorage.query.filter_by(
            storage_unit_id=None, location=row.location, level=row.level, box=row.box
        )
        .order_by(PartStorage.id)
        .all()
    )
    images = catalog_images({item.part_num for item in rows})
    return legacy_storage_groups(
        _overview_locations(), [content_dict(item, images) for item in rows]
    )[0]


def content_options():
    # Explicitly requested by editing forms, never on initial page load.
    return [
        content_dict(row) for row in PartStorage.query.order_by(PartStorage.id).all()
    ]


def overview(focused=False, shelf_id=None, all_shelves=False):
    locations = _overview_locations()
    selected_shelf = None
    if focused and not all_shelves:
        shelves = [row for row in locations if row["kind"] == "shelf"]
        by_id = {row["id"]: row for row in locations}

        def path(row):
            labels = [row["label"]]
            parent = by_id.get(row["parent_id"])
            while parent:
                labels.insert(0, parent["label"])
                parent = by_id.get(parent["parent_id"])
            return _natural_label(" / ".join(labels))

        shelves.sort(key=path)
        selected_shelf = next(
            (row["id"] for row in shelves if row["id"] == shelf_id),
            shelves[0]["id"] if shelves else None,
        )
    # Raw scalar projection avoids loading catalogs for every unselected shelf.
    raw = [
        dict(row)
        for row in db.session.execute(
            db.select(db.metadata.tables["part_storage"]).order_by(PartStorage.id)
        ).mappings()
    ]
    groups = legacy_storage_groups(locations, raw)
    summary = {
        "legacy_rows": sum(group["row_count"] for group in groups),
        "legacy_groups": len(groups),
        "unlocated_legacy_rows": sum(
            group["row_count"] for group in groups if group["shelf_id"] is None
        ),
        "content_rows": len(raw),
    }
    visible_ids = None
    if focused and not all_shelves:
        visible_ids = {
            identifier
            for group in groups
            if group["shelf_id"] == selected_shelf and selected_shelf is not None
            for identifier in group["storage_ids"]
        }
        # Preserve confirmed-unit editing and navigation across shelves.
        visible_ids.update(
            row["id"] for row in raw if row["storage_unit_id"] is not None
        )
    query = PartStorage.query.order_by(PartStorage.id)
    if visible_ids is not None:
        query = query.filter(PartStorage.id.in_(visible_ids))
    rows = query.all()
    images = catalog_images({row.part_num for row in rows})
    contents = [content_dict(row, images) for row in rows]
    if not focused or all_shelves:
        visible_groups = legacy_storage_groups(locations, contents)
    else:
        visible_groups = legacy_storage_groups(locations, contents)
        # Unresolved addresses remain discoverable, without their potentially huge contents.
        for group in groups:
            if group["shelf_id"] is None:
                visible_groups.append(
                    {key: value for key, value in group.items() if key != "contents"}
                )
    return {
        "locations": locations,
        "types": [
            serialize(row)
            for row in ContainerType.query.order_by(ContainerType.id).all()
        ],
        "units": [
            unit_details(row.id)
            for row in StorageUnit.query.filter_by(active=True)
            .order_by(StorageUnit.id)
            .all()
        ],
        "placements": [serialize(row) for row in StoragePlacement.query.all()],
        "stack_rules": [serialize(row) for row in StackRule.query.all()],
        "contents": contents,
        "legacy_groups": visible_groups,
        "legacy_summary": summary,
        "focused": focused,
        "selected_shelf_id": selected_shelf,
    }


def legacy_guard(entry=None, *, part_num=None, color_id=None, exact_color=False):
    """Never let an old single-location writer mutate counted/physical storage."""
    if entry is not None:
        candidates = [entry]
    else:
        query = PartStorage.query.filter_by(part_num=part_num)
        if exact_color:
            query = query.filter_by(color_id=color_id)
        candidates = query.all()
    if len(candidates) > 1 or any(
        c.storage_unit_id is not None or c.quantity is not None for c in candidates
    ):
        raise Conflict(
            "Mehrdeutiger oder strukturierter Fundort: Lagerverwaltung verwenden."
        )
    return candidates[0] if candidates else None


def guard_legacy_request():
    """Protect old writers even when their legacy response logic remains intact."""
    from flask import jsonify, request

    if request.method not in {"POST", "PUT", "DELETE"}:
        return None
    endpoint = request.endpoint or ""
    singles = {
        "set_maintain.update_part_location",
        "upload.save_storage_location",
    }
    explicit = {
        "box_maintenance.update_part_location",
        "box_maintenance.delete_part_storage",
        "manual_entry.delete_storage",
    }
    try:
        if endpoint in singles:
            payload = request.get_json(silent=True)
            if isinstance(payload, dict):
                part_num = (request.view_args or {}).get("part_num") or payload.get(
                    "part_num"
                )
                if part_num:
                    legacy_guard(
                        part_num=part_num,
                        color_id=payload.get("color_id"),
                        exact_color=endpoint.startswith("client_api."),
                    )
        elif endpoint in explicit:
            payload = request.get_json(silent=True) or {}
            identifier = (request.view_args or {}).get("storage_id") or (
                payload.get("storage_id") if isinstance(payload, dict) else None
            )
            if isinstance(identifier, int):
                entry = db.session.get(PartStorage, identifier)
                if entry:
                    legacy_guard(entry)
                    if request.method == "DELETE":
                        mapping = db.session.get(LegacyStorageMapping, entry.id)
                        if mapping and not mapping.confirmed:
                            db.session.delete(mapping)
        elif endpoint == "storage.add_to_storage":
            legacy_guard(part_num=(request.view_args or {}).get("part_id"))
        elif endpoint in {
            "part_location.save_locations",
            "part_location.delete_location",
        }:
            payload = request.get_json(silent=True)
            if isinstance(payload, dict):
                parts = (
                    [payload.get("part_num")]
                    if endpoint.endswith("delete_location")
                    else payload.keys()
                )
                for part_num in parts:
                    if part_num:
                        legacy_guard(part_num=part_num)
        elif endpoint == "manual_entry.manual_entry":
            for part_num in request.form.get("part_num", "").split(","):
                row = PartStorage.query.filter_by(
                    part_num=part_num.strip(),
                    location=request.form.get("schrank"),
                    level=request.form.get("fach"),
                    box=request.form.get("box"),
                ).first()
                if row:
                    legacy_guard(row)
    except Conflict as error:
        return jsonify({"error": error.description, "warehouse_url": "/warehouse"}), 409
    return None


def unit_label_info(identifier):
    """Reuse existing label renderers with unambiguous physical unit identity."""
    unit = get(StorageUnit, identifier)
    address = unit_address(identifier)
    by_kind = {p["kind"]: p["label"] for p in address["location_path"]}
    items = []
    contents = (
        PartStorage.query.filter_by(storage_unit_id=identifier)
        .order_by(PartStorage.part_num)
        .all()
    )
    images = catalog_images({row.part_num for row in contents})
    for content in contents:
        part = db.session.get(RebrickableParts, content.part_num)
        items.append(
            {
                "part_num": content.part_num,
                "name": part.name if part else "Katalogdaten fehlen",
                "category": part.category.name
                if part and part.category
                else "Unbekannt",
                "img_url": content_dict(content, images)["part_img_url"],
            }
        )
    return {
        "unit_id": unit.id,
        "location": by_kind.get("rack", "?"),
        "level": by_kind.get("shelf", "?"),
        "box": unit.label,
        "items": items,
    }
