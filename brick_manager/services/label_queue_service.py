"""Explicit, durable reprint requests, separate from historical print status."""

import hashlib
import json
from uuid import uuid4

from models import ConfigSettings, PartStorage, StorageUnit, db
from werkzeug.exceptions import BadRequest, Conflict, NotFound

from services import storage_service

PREFIX = "warehouse_label_request:"


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _key(target):
    return PREFIX + hashlib.sha256(_json(target).encode()).hexdigest()


def _target(data):
    if data.get("unit_id") is not None:
        identifier = storage_service.integer(data["unit_id"], "unit_id")
        unit = storage_service.get(StorageUnit, identifier)
        if not unit.active:
            raise Conflict("Behälter ist nicht aktiv.")
        return {"unit_id": identifier}
    identifier = storage_service.integer(data.get("storage_id"), "storage_id")
    row = storage_service.get(PartStorage, identifier)
    if row.storage_unit_id is not None:
        return _target({"unit_id": row.storage_unit_id})
    values = [row.location, row.level, row.box]
    if any(not isinstance(v, str) or not v.strip() for v in values):
        raise BadRequest("Für den Druck zuerst Schrank, Fach und Box zuordnen.")
    return dict(zip(("location", "level", "box"), values, strict=True))


def set_mark(data):
    if not isinstance(data.get("marked"), bool):
        raise BadRequest("marked muss ein Wahrheitswert sein.")
    target = _target(data)
    key = _key(target)
    row = ConfigSettings.query.filter_by(key=key).first()
    if data["marked"]:
        if row is None:
            row = ConfigSettings()
            row.key = key
            row.encrypted = False
            db.session.add(row)
        row.value = _json({"target": target, "generation": uuid4().hex})
    elif row is not None:
        db.session.delete(row)
    db.session.commit()
    return {"target": target, "marked": data["marked"]}


def _info(target):
    if "unit_id" in target:
        return storage_service.unit_label_info(target["unit_id"])
    rows = (
        PartStorage.query.filter_by(**target, storage_unit_id=None)
        .order_by(PartStorage.id)
        .all()
    )
    if not rows:
        raise Conflict("Vorgemerkte Box wurde geändert. Vormerkung im Lager prüfen.")
    images = storage_service.catalog_images({row.part_num for row in rows})
    items = {}
    for row in rows:
        part = row.rebrickable_part
        items[(row.part_num, row.color_id)] = {
            "part_num": row.part_num,
            "name": part.name if part else "Katalogdaten fehlen",
            "category": part.category.name if part and part.category else "Unbekannt",
            "img_url": storage_service.content_dict(row, images)["part_img_url"],
        }
    return {
        **target,
        "items": list(items.values()),
        "source_ids": [row.id for row in rows],
    }


def marks():
    result = []
    for row in (
        ConfigSettings.query.filter(ConfigSettings.key.startswith(PREFIX))
        .order_by(ConfigSettings.id)
        .all()
    ):
        value = json.loads(row.value)
        target = value["target"]
        entry = {"key": row.key, **value}
        try:
            info = _info(target)
            entry["fingerprint"] = hashlib.sha256(_json(info).encode()).hexdigest()
            entry["label"] = (
                f"Schrank {info['location']} / Fach {info['level']} / Box {info['box']}"
            )
            entry["error"] = None
        except (Conflict, NotFound) as error:
            entry.update(
                fingerprint=None, label="Fundort prüfen", error=error.description
            )
        result.append(entry)
    return result


def selected(data):
    supplied = data.get("marks")
    if not isinstance(supplied, list) or not 1 <= len(supplied) <= 1000:
        raise BadRequest("Zwischen 1 und 1000 Vormerkungen auswählen.")
    current = {entry["key"]: entry for entry in marks()}
    result = []
    seen = set()
    for entry in supplied:
        if not isinstance(entry, dict) or not isinstance(entry.get("key"), str):
            raise BadRequest("Ungültige Vormerkung.")
        key = entry["key"]
        if key in seen:
            raise BadRequest("Doppelte Vormerkung.")
        seen.add(key)
        actual = current.get(key)
        if (
            actual is None
            or actual["error"]
            or any(
                entry.get(field) != actual[field]
                for field in ("generation", "fingerprint")
            )
        ):
            raise Conflict(
                "Vormerkung oder Boxinhalt geändert. Liste neu laden und erneut drucken."
            )
        result.append(actual)
    return result


def label_infos(data):
    return [_info(entry["target"]) for entry in selected(data)]


def confirm(data):
    # Serialize with concurrent marking/content changes before snapshot validation.
    if db.engine.dialect.name == "sqlite":
        db.session.execute(db.text("BEGIN IMMEDIATE"))
    entries = selected(data)
    for entry in entries:
        target = entry["target"]
        if "unit_id" in target:
            unit = storage_service.get(StorageUnit, target["unit_id"])
            unit.label_printed = True
            unit.revision += 1
        else:
            PartStorage.query.filter_by(**target, storage_unit_id=None).update(
                {PartStorage.label_printed: True}, synchronize_session=False
            )
        db.session.delete(ConfigSettings.query.filter_by(key=entry["key"]).one())
    db.session.commit()
    return {"confirmed": len(entries)}


def remove(data):
    key = data.get("key")
    if not isinstance(key, str) or not key.startswith(PREFIX):
        raise BadRequest("Ungültige Vormerkung.")
    row = ConfigSettings.query.filter_by(key=key).first()
    if row is not None:
        value = json.loads(row.value)
        if value["generation"] != data.get("generation"):
            raise Conflict("Vormerkung wurde geändert. Liste neu laden.")
        db.session.delete(row)
        db.session.commit()
    return {"removed": True}
