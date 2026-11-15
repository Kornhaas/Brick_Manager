# pyright: reportCallIssue=false
# Flask-SQLAlchemy generates keyword constructors not visible to static analysis.
"""Reserved, auditable movements with atomic, idempotent physical confirmation."""

from __future__ import annotations

from datetime import UTC, datetime

from models import (
    ContainerType,
    PartStorage,
    RebrickableColors,
    RebrickableParts,
    StackRule,
    StorageLocation,
    StorageMove,
    StorageMoveItem,
    StoragePlacement,
    StorageUnit,
    db,
)
from sqlalchemy import text as sql_text
from werkzeug.exceptions import BadRequest, Conflict, NotFound

from services.storage_service import (
    _content_target,
    _placement_data,
    choice,
    commit,
    get,
    integer,
    preview_placement,
    serialize,
    space_report,
    text,
    unit_address,
)


def move_dict(move):
    result = serialize(move)
    result["preview"] = (
        (move.snapshot or {}).get("effects", [])
        if move.status in {"confirmed", "cancelled"}
        else _effect_preview(move)
    )
    result["items"] = [
        serialize(i)
        for i in StorageMoveItem.query.filter_by(move_id=move.id)
        .order_by(StorageMoveItem.ordinal)
        .all()
    ]
    return result


def list_moves():
    return [
        move_dict(m) for m in StorageMove.query.order_by(StorageMove.id.desc()).all()
    ]


def _locked(identifier):
    """Acquire SQLite's write lock before inspecting reservations or versions."""
    integer(identifier, "move_id")
    db.session.execute(
        sql_text("UPDATE storage_moves SET revision = revision WHERE id = :id"),
        {"id": identifier},
    )
    db.session.expire_all()
    return get(StorageMove, identifier)


def _entries(move):
    return move.payload["items"]


def create_move(data):
    kind = choice(data.get("kind"), {"unit", "quantity", "intake"}, "kind")
    key = text(data.get("idempotency_key"), "idempotency_key")
    raw = data.get("items", [data])
    if not isinstance(raw, list) or not raw or len(raw) > 100:
        raise BadRequest("Ein bis 100 Arbeitsschritte erforderlich.")
    entries = []
    for item in raw:
        if not isinstance(item, dict):
            raise BadRequest("Arbeitsschritt muss ein Objekt sein.")
        if kind == "unit":
            unit = get(StorageUnit, item.get("unit_id"))
            target = item.get("target_placement")
            if not isinstance(target, dict):
                raise BadRequest("Zielaufstellung erforderlich.")
            remove = target.get("remove") is True
            values = {"remove": True} if remove else _placement_data(unit.id, target)
            entries.append({"unit_id": unit.id, "target_placement": values})
        else:
            target = _content_target(item.get("target_unit_id"))
            quantity = integer(item.get("quantity"), "quantity")
            entry = {"target_unit_id": target.id, "quantity": quantity}
            if kind == "quantity":
                source = get(PartStorage, item.get("storage_id"))
                if (
                    source.storage_unit_id is None
                    or source.color_id is None
                    or source.quantity is None
                ):
                    raise Conflict(
                        "Quelle zuerst zuordnen, Farbe bestimmen und zählen."
                    )
                if source.storage_unit_id == target.id:
                    raise BadRequest("Quelle und Ziel müssen verschieden sein.")
                entry["storage_id"] = source.id
            else:
                part_num = text(item.get("part_num"), "part_num")
                if db.session.get(RebrickableParts, part_num) is None:
                    raise NotFound("Bricks-Teil nicht gefunden.")
                color_id = integer(item.get("color_id"), "color_id", 0)
                if db.session.get(RebrickableColors, color_id) is None:
                    raise NotFound("Farbe nicht gefunden.")
                entry.update(part_num=part_num, color_id=color_id)
            entries.append(entry)
    if kind == "unit" and len({entry["unit_id"] for entry in entries}) != len(entries):
        raise BadRequest("Ein Behälter darf pro Auftrag nur ein Ziel haben.")
    payload = {"items": entries}
    if data.get("depends_on_move_id") is not None:
        payload["depends_on_move_id"] = get(StorageMove, data["depends_on_move_id"]).id
    reason = text(data.get("reason", "Physische Lagerbewegung"), "reason")
    existing = StorageMove.query.filter_by(idempotency_key=key).first()
    if existing:
        if (
            existing.payload != payload
            or existing.kind != kind
            or existing.reason != reason
        ):
            raise Conflict("Idempotenzschlüssel gehört zu einem anderen Auftrag.")
        return move_dict(existing)
    move = StorageMove(
        kind=kind, idempotency_key=key, reason=reason, payload=payload, status="draft"
    )
    db.session.add(move)
    db.session.flush()
    for order, entry in enumerate(entries):
        db.session.add(
            StorageMoveItem(
                move_id=move.id,
                ordinal=order,
                **{
                    k: v
                    for k, v in entry.items()
                    if k
                    in {
                        "unit_id",
                        "storage_id",
                        "target_unit_id",
                        "quantity",
                        "target_placement",
                    }
                },
            )
        )
    commit()
    return move_dict(move)


def _unit_closure(unit_id):
    """Include containing drawers, all support ancestors and their versions."""
    result = set()
    while unit_id is not None:
        if unit_id in result:
            raise Conflict("Zyklus in Lagerstruktur.")
        result.add(unit_id)
        unit = get(StorageUnit, unit_id)
        placement = db.session.get(StoragePlacement, unit_id)
        unit_id = unit.host_unit_id or (
            placement.support_unit_id if placement else None
        )
    return result


def _snapshot(move):
    unit_ids = set()
    contents = {}
    locations = {}
    quantity_used = {}
    moving = {i["unit_id"] for i in _entries(move) if "unit_id" in i}
    previews = []
    for entry in _entries(move):
        if move.kind == "unit":
            unit = get(StorageUnit, entry["unit_id"])
            if unit.host_unit_id:
                raise Conflict(
                    "Schubladen folgen ihrem Magazin; Inhalt getrennt umbuchen."
                )
            above = {
                p.unit_id
                for p in StoragePlacement.query.filter_by(support_unit_id=unit.id).all()
            }
            if above - moving:
                raise Conflict(
                    "Aufliegende Behälter zuerst abnehmen oder ausdrücklich mitbewegen."
                )
            unit_ids |= _unit_closure(unit.id)
            # Magazine contents travel with their fixed drawer/compartment identities.
            pending = [unit.id]
            descendants = set()
            while pending:
                current = pending.pop()
                if current in descendants:
                    continue
                descendants.add(current)
                pending.extend(
                    u.id
                    for u in StorageUnit.query.filter_by(
                        host_unit_id=current, active=True
                    ).all()
                )
            unit_ids |= descendants
            for row in PartStorage.query.filter(
                PartStorage.storage_unit_id.in_(descendants)
            ).all():
                contents[str(row.id)] = row.revision
            target = entry["target_placement"]
            if target.get("remove"):
                if (
                    any(
                        not get(StorageUnit, uid).contents_complete
                        for uid in descendants
                    )
                    or PartStorage.query.filter(
                        PartStorage.storage_unit_id.in_(descendants)
                    )
                    .filter(
                        (PartStorage.quantity.is_(None)) | (PartStorage.quantity > 0)
                    )
                    .first()
                    or above
                ):
                    raise Conflict(
                        "Nur vollständig leere, freie Behälter aus Aufstellung entfernen; sonst Zielort angeben."
                    )
                previews.append({"status": "fits", "reasons": []})
            else:
                preview = preview_placement(unit.id, target)
                if preview["status"] == "no_fit":
                    raise Conflict("Ziel passt nicht: " + "; ".join(preview["reasons"]))
                previews.append(preview)
                if target.get("support_unit_id"):
                    if target["support_unit_id"] in moving:
                        raise Conflict(
                            "Auflage und obere Einheit in getrennten bestätigten Schritten umstellen."
                        )
                    unit_ids |= _unit_closure(target["support_unit_id"])
                if target.get("shelf_id"):
                    for loc in _location_ancestors(target["shelf_id"]):
                        locations[str(loc.id)] = loc.revision
        else:
            target = _content_target(entry["target_unit_id"])
            if target.fill_state == "full":
                raise Conflict(
                    "Ziel ist voll. Größeren Behälter oder zweiten Ort wählen."
                )
            unit_ids |= _unit_closure(target.id)
            if move.kind == "quantity":
                source = get(PartStorage, entry["storage_id"])
                if (
                    source.quantity is None
                    or source.color_id is None
                    or source.storage_unit_id is None
                ):
                    raise Conflict("Quelle unvollständig erfasst.")
                quantity_used[source.id] = (
                    quantity_used.get(source.id, 0) + entry["quantity"]
                )
                if quantity_used[source.id] > source.quantity:
                    raise Conflict("Nicht genügend Bestand am Quellort.")
                contents[str(source.id)] = source.revision
                unit_ids |= _unit_closure(source.storage_unit_id)
                part, color = source.part_num, source.color_id
            else:
                part, color = entry["part_num"], entry["color_id"]
            rows = PartStorage.query.filter_by(
                storage_unit_id=target.id, part_num=part, color_id=color
            ).all()
            # Unknown-colour contents cannot safely be treated as a separate known lot.
            ambiguous = PartStorage.query.filter_by(
                storage_unit_id=target.id, part_num=part, color_id=None
            ).first()
            if ambiguous or any(row.quantity is None for row in rows):
                raise Conflict(
                    "Vorhandenen Zielbestand zuerst identifizieren und zählen."
                )
            for row in rows:
                contents[str(row.id)] = row.revision
    units = {str(uid): get(StorageUnit, uid).revision for uid in sorted(unit_ids)}
    placements = {}
    types = {}
    for uid in unit_ids:
        unit = get(StorageUnit, uid)
        if unit.type_id:
            types[str(unit.type_id)] = serialize(get(ContainerType, unit.type_id))
        placement = db.session.get(StoragePlacement, uid)
        placements[str(uid)] = serialize(placement) if placement else None
        address = unit_address(uid)
        if address["shelf_id"]:
            for loc in _location_ancestors(address["shelf_id"]):
                locations[str(loc.id)] = loc.revision
    # Initial/current layouts cannot detect collisions between two future destinations.
    destinations = [
        i
        for i in _entries(move)
        if i.get("target_placement", {}).get("shelf_id")
        or i.get("target_placement", {}).get("support_unit_id")
    ]
    for index, left in enumerate(destinations):
        lp = left["target_placement"]
        for right in destinations[index + 1 :]:
            rp = right["target_placement"]
            if (lp["shelf_id"], lp["support_unit_id"]) != (
                rp["shelf_id"],
                rp["support_unit_id"],
            ):
                continue
            if (
                lp["support_unit_id"]
                and lp["relation_kind"] == rp["relation_kind"] == "stacked"
            ):
                raise Conflict(
                    "Eine Stapelposition kann nur einen nächsten Behälter tragen."
                )
            from services.storage_service import _dimensions

            lw, ld, _lh, _lv = _dimensions(get(StorageUnit, left["unit_id"]))
            rw, rd, _rh, _rv = _dimensions(get(StorageUnit, right["unit_id"]))
            if lp["orientation"] == "rotated":
                lw, ld = ld, lw
            if rp["orientation"] == "rotated":
                rw, rd = rd, rw
            if None in (
                lp["x_mm"],
                lp["depth_offset_mm"],
                rp["x_mm"],
                rp["depth_offset_mm"],
                lw,
                ld,
                rw,
                rd,
            ):
                if lp["order_left"] == rp["order_left"]:
                    raise Conflict(
                        "Mehrere Einheiten beanspruchen dieselbe geplante Stellposition."
                    )
            elif (
                lp["x_mm"] < rp["x_mm"] + rw
                and rp["x_mm"] < lp["x_mm"] + lw
                and lp["depth_offset_mm"] < rp["depth_offset_mm"] + rd
                and rp["depth_offset_mm"] < lp["depth_offset_mm"] + ld
            ):
                raise Conflict("Geplante Zielstellflächen überlappen.")
    return {
        "units": units,
        "contents": contents,
        "placements": placements,
        "types": types,
        "rules": [
            {
                key: value
                for key, value in serialize(rule).items()
                if key != "verified_at"
            }
            for rule in StackRule.query.order_by(StackRule.id).all()
        ],
        "locations": locations,
        "previews": previews,
    }


def _location_ancestors(identifier):
    result = []
    seen = set()
    while identifier:
        if identifier in seen:
            raise Conflict("Zyklus in Orten.")
        seen.add(identifier)
        loc = get(StorageLocation, identifier)
        result.append(loc)
        identifier = loc.parent_id
    return result


def _reserve(move, snapshot):
    for other in StorageMove.query.filter(
        StorageMove.status == "planned", StorageMove.id != move.id
    ).all():
        saved = other.snapshot or {}
        # Whole involved units are reserved; conservative and independent of quantities.
        if set(snapshot["units"]) & set(saved.get("units", {})):
            raise Conflict("Quelle oder Ziel ist bereits reserviert.")
        destination_shelves = {
            str(i["target_placement"]["shelf_id"])
            for i in _entries(move)
            if i.get("target_placement", {}).get("shelf_id")
            or i.get("target_placement", {}).get("support_unit_id")
            or i.get("target_placement", {}).get("support_unit_id")
        }
        other_shelves = {
            str(i["target_placement"]["shelf_id"])
            for i in _entries(other)
            if i.get("target_placement", {}).get("shelf_id")
            or i.get("target_placement", {}).get("support_unit_id")
            or i.get("target_placement", {}).get("support_unit_id")
        }
        if destination_shelves & other_shelves:
            raise Conflict("Zielstellfläche ist bereits für einen Plan reserviert.")


def plan_move(identifier):
    move = _locked(identifier)
    if move.status == "planned":
        return move_dict(move)
    if move.status != "draft":
        raise Conflict("Nur ein Entwurf kann geplant werden.")
    dependency = move.payload.get("depends_on_move_id")
    if dependency and get(StorageMove, dependency).status != "confirmed":
        raise Conflict("Vorausgehende Bewegung zuerst bestätigen.")
    snapshot = _snapshot(move)
    _reserve(move, snapshot)
    move.snapshot = snapshot
    move.status = "planned"
    move.revision += 1
    for item in StorageMoveItem.query.filter_by(move_id=move.id).all():
        item.source_snapshot = snapshot
        if item.storage_id:
            item.source_revision = get(PartStorage, item.storage_id).revision
        elif item.unit_id:
            item.source_revision = get(StorageUnit, item.unit_id).revision
    commit()
    result = move_dict(move)
    result["preview"] = _effect_preview(move)
    return result


def _effect_preview(move):
    results = []
    for item in _entries(move):
        if move.kind == "unit":
            unit = get(StorageUnit, item["unit_id"])
            placement = db.session.get(StoragePlacement, unit.id)
            results.append(
                {
                    "unit_id": unit.id,
                    "container_emptied": False,
                    "stack_lowered": bool(placement and placement.support_unit_id),
                    "base_area_released": bool(
                        placement
                        and placement.shelf_id
                        and any(
                            item["target_placement"].get(field)
                            != getattr(placement, field)
                            for field in (
                                "shelf_id",
                                "support_unit_id",
                                "x_mm",
                                "depth_offset_mm",
                                "orientation",
                            )
                        )
                    ),
                    "measurement_note": "Nur gemessene zusammenhängende Grundfläche erlaubt eine Passzusage.",
                }
            )
        elif move.kind == "quantity":
            source = get(PartStorage, item["storage_id"])
            results.append(
                {
                    "storage_id": source.id,
                    "container_emptied": source.quantity
                    == sum(
                        i["quantity"]
                        for i in _entries(move)
                        if i.get("storage_id") == source.id
                    )
                    and get(StorageUnit, source.storage_unit_id).contents_complete
                    and not PartStorage.query.filter(
                        PartStorage.storage_unit_id == source.storage_unit_id,
                        PartStorage.id != source.id,
                        (PartStorage.quantity.is_(None)) | (PartStorage.quantity > 0),
                    ).first(),
                    "stack_lowered": False,
                    "base_area_released": False,
                    "measurement_note": "Leere Hülle bleibt am Ort und belegt Stellfläche.",
                }
            )
    return results


def confirm_move(identifier, data=None):
    data = data or {}
    move = _locked(identifier)
    if (
        data.get("idempotency_key") is not None
        and data["idempotency_key"] != move.idempotency_key
    ):
        raise Conflict("Bestätigung gehört zu einem anderen Auftrag.")
    if move.status == "confirmed":
        return move_dict(move)
    if move.status != "planned":
        raise Conflict("Auftrag zuerst planen.")
    if (
        data.get("revision") is not None
        and integer(data["revision"], "revision") != move.revision
    ):
        raise Conflict("Planrevision ist veraltet.")
    current = _snapshot(move)
    if current != move.snapshot:
        raise Conflict(
            "Bestand, Aufstellung oder Maße haben sich geändert. Neu planen."
        )
    _reserve(move, current)
    if (
        any(p["status"] == "unknown" for p in current["previews"])
        and data.get("physical_fit_confirmed") is not True
    ):
        raise Conflict("Unbekannte Passung zuerst vor Ort prüfen und bestätigen.")
    if (
        move.kind in {"quantity", "intake"}
        and any(
            get(StorageUnit, i["target_unit_id"]).fill_state != "space"
            for i in _entries(move)
        )
        and data.get("capacity_confirmed") is not True
    ):
        raise Conflict("Zielkapazität vor Ort prüfen und bestätigen.")
    source_shelves = set()
    for uid in current["units"]:
        sid = unit_address(int(uid))["shelf_id"]
        if sid:
            source_shelves.add(sid)
    for entry in _entries(move):
        target_shelf = entry.get("target_placement", {}).get("shelf_id")
        if target_shelf:
            source_shelves.add(target_shelf)
    effects = _effect_preview(move)
    before = {str(sid): space_report(sid) for sid in source_shelves}
    try:
        for item in _entries(move):
            if move.kind == "unit":
                placement = db.session.get(StoragePlacement, item["unit_id"])
                if item["target_placement"].get("remove"):
                    if placement:
                        db.session.delete(placement)
                elif placement is None:
                    db.session.add(
                        StoragePlacement(
                            unit_id=item["unit_id"], **item["target_placement"]
                        )
                    )
                else:
                    for field, value in item["target_placement"].items():
                        setattr(placement, field, value)
                    placement.revision += 1
            else:
                if move.kind == "quantity":
                    source = get(PartStorage, item["storage_id"])
                    part, color = source.part_num, source.color_id
                    source.quantity -= item["quantity"]
                    source.revision += 1
                else:
                    part, color = item["part_num"], item["color_id"]
                destination = (
                    PartStorage.query.filter_by(
                        storage_unit_id=item["target_unit_id"],
                        part_num=part,
                        color_id=color,
                    )
                    .order_by(PartStorage.id)
                    .first()
                )
                if destination is None:
                    destination = PartStorage(
                        storage_unit_id=item["target_unit_id"],
                        part_num=part,
                        color_id=color,
                        quantity=0,
                        migration_status="confirmed",
                    )
                    db.session.add(destination)
                destination.quantity += item["quantity"]
                destination.revision = (destination.revision or 1) + 1
        for uid in current["units"]:
            unit = get(StorageUnit, int(uid))
            unit.revision += 1
            unit.label_printed = False
        for item in StorageMoveItem.query.filter_by(move_id=move.id).all():
            item.status = "confirmed"
        for sid in source_shelves:
            get(StorageLocation, sid).revision += 1
        move.status = "confirmed"
        move.revision += 1
        move.confirmed_at = datetime.now(UTC).replace(tzinfo=None)
        db.session.flush()
        after = {str(sid): space_report(sid) for sid in source_shelves}
        move.snapshot = {
            **current,
            "effects": effects,
            "space_before": before,
            "space_after": after,
            "physical_fit_confirmed": data.get("physical_fit_confirmed") is True,
            "capacity_confirmed": data.get("capacity_confirmed") is True,
        }
        commit()
    except Exception:
        db.session.rollback()
        raise
    return move_dict(move)


def cancel_move(identifier):
    move = _locked(identifier)
    if move.status == "confirmed":
        raise Conflict("Bestätigte Bewegung nur durch neuen Gegenauftrag umkehren.")
    if move.status != "cancelled":
        move.status = "cancelled"
        move.revision += 1
        for item in StorageMoveItem.query.filter_by(move_id=identifier).all():
            item.status = "cancelled"
        commit()
    return move_dict(move)
