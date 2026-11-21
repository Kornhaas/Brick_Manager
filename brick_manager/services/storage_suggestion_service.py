"""Explainable archive review and intake rules for Bricks storage."""

import hashlib
import json
from collections import Counter
from datetime import date, datetime

from models import (
    CatalogGeneration,
    CategoryStorageRule,
    ConfigSettings,
    PartStorage,
    PartStoragePreference,
    PlannedSet,
    RebrickableColors,
    RebrickableInventories,
    RebrickableInventoryMinifigs,
    RebrickableInventoryParts,
    RebrickableInventorySets,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    StorageLocation,
    StoragePlacement,
    StorageUnit,
    User_Parts,
    UserMinifigurePart,
    db,
)
from werkzeug.exceptions import BadRequest, NotFound

from services.part_history_service import catalog_status, part_history, rule_number

MANUAL_REVIEW_HINT = "Eigenbedarf unbekannt · bitte prüfen"
DEFAULTS = {"max_known_sets": 2, "min_age_years": 10, "catalog_max_age_days": 90}


def _integer(value, name, *, minimum=0, nullable=False):
    if nullable and value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BadRequest(f"{name} must be an integer >= {minimum}.")
    return value


def _body(data):
    if not isinstance(data, dict):
        raise BadRequest("A JSON object is required.")
    return data


def _setting(key):
    return ConfigSettings.query.filter_by(
        key=f"warehouse.{key}", encrypted=False
    ).first()


def _put_setting(key, value):
    row = _setting(key)
    if row is None:
        row = ConfigSettings()
        row.key = f"warehouse.{key}"
        row.encrypted = False
        db.session.add(row)
    row.value = str(value)


def _planning_signature():
    generation = CatalogGeneration.query.order_by(CatalogGeneration.id.desc()).first()
    snapshot = {
        "plans": [
            (r.id, r.set_num, r.quantity, r.active, r.revision)
            for r in PlannedSet.query.order_by(PlannedSet.id).all()
        ],
        "catalog": (generation.id, generation.revision) if generation else None,
    }
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def _reviewed():
    state = _setting("planning_reviewed")
    signature = _setting("planning_signature")
    return bool(
        state
        and state.value == "true"
        and signature
        and signature.value == _planning_signature()
    )


def _inventory_counts(entity, path=frozenset()) -> tuple[Counter, set[str], int | None]:
    """Use one fully resolvable version, including child quantities once per edge."""
    if entity in path:
        return Counter(), {"Zyklus im geplanten Inventar"}, None
    versions = (
        RebrickableInventories.query.filter_by(set_num=entity)
        .order_by(
            RebrickableInventories.version.desc(), RebrickableInventories.id.desc()
        )
        .all()
    )
    if not versions:
        return Counter(), {"Geplantes Set-/Figureninventar fehlt"}, None
    best = None
    for version in versions:
        counts = Counter()
        missing = set()
        direct = RebrickableInventoryParts.query.filter_by(
            inventory_id=version.id, is_spare=False
        ).all()
        for row in direct:
            if row.quantity <= 0:
                continue
            if (
                db.session.get(RebrickableParts, row.part_num) is None
                or db.session.get(RebrickableColors, row.color_id) is None
            ):
                missing.add("Geplante Teil-/Farbverknüpfung fehlt")
            counts[(row.part_num, row.color_id)] += row.quantity
        children = [
            (r.set_num, r.quantity)
            for r in RebrickableInventorySets.query.filter_by(
                inventory_id=version.id
            ).all()
        ]
        children.extend(
            (r.fig_num, r.quantity)
            for r in RebrickableInventoryMinifigs.query.filter_by(
                inventory_id=version.id
            ).all()
        )
        for child, multiplier in children:
            if multiplier <= 0:
                continue
            child_counts, problems, _ = _inventory_counts(child, path | {entity})
            missing.update(problems)
            for key, quantity in child_counts.items():
                counts[key] += quantity * multiplier
        if not direct and not children:
            missing.add("Geplantes Inventar ohne erfassten Inhalt")
        result = (counts, missing, version.version)
        if not missing:
            return result
        if best is None:
            best = result
    return best if best is not None else (Counter(), {"Geplantes Inventar fehlt"}, None)


def part_demand(part_num, color_id, as_of=None):
    """Known positive demand protects a variant even if other plans are unknown."""
    missing = set()
    open_quantity = 0
    for model in (User_Parts, UserMinifigurePart):
        for row in model.query.filter_by(part_num=part_num, color_id=color_id).all():
            if not row.is_spare:
                open_quantity += max(row.quantity - (row.have_quantity or 0), 0)
    planned_quantity = 0
    versions = []
    for planned in (
        PlannedSet.query.filter_by(active=True).order_by(PlannedSet.id).all()
    ):
        counts, problems, version = _inventory_counts(planned.set_num)
        missing.update(problems)
        planned_quantity += counts[(part_num, color_id)] * planned.quantity
        versions.append(
            {
                "planned_set_id": planned.id,
                "set_num": planned.set_num,
                "version": version,
                "quantity": planned.quantity,
            }
        )
    provenance = catalog_status(as_of)
    if not provenance["complete"]:
        missing.add("Bedarfsinventare nicht vollständig geprüft")
    if not _reviewed():
        missing.add("Eigenbedarf unbekannt")
    if color_id is None:
        missing.add("Farbe unbestimmt")
    status = (
        "positive"
        if planned_quantity or open_quantity
        else ("unknown" if missing else "none")
    )
    return {
        "status": status,
        "planned_quantity": planned_quantity,
        "open_quantity": open_quantity,
        "missing": sorted(missing),
        "versions": versions,
        "reviewed": _reviewed(),
    }


def classify_variant(part_num, color_id, as_of=None):
    history = part_history(part_num, color_id, as_of)
    demand = part_demand(part_num, color_id, as_of)
    preference = PartStoragePreference.query.filter_by(
        part_num=part_num, color_id=color_id
    ).first()
    today = as_of or date.today()
    if isinstance(today, datetime):
        today = today.date()
    reasons = []
    classification = "keep_accessible"
    if preference and preference.keep_accessible:
        reasons.append("Manuell griffbereit halten")
    elif demand["status"] == "positive":
        reasons.append("Bekannter Eigenbedarf")
    elif not history["complete"]:
        reasons.append("Katalogdaten unvollständig")
    elif history["known_set_count"] > rule_number("max_known_sets", 2):
        reasons.append("Bekannte Set-Anzahl über Archivgrenze")
    elif history["last_year"] is None or today.year - history[
        "last_year"
    ] < rule_number("min_age_years", 10):
        reasons.append("Neue oder aktuell vorkommende Variante – griffbereit lagern")
    else:
        classification = (
            "manual_archive_review"
            if demand["status"] == "unknown"
            else "archive_candidate"
        )
        reasons.append(
            f"{history['known_set_count']} bekannte Sets; letztes bekanntes Set-Jahr {history['last_year']}"
        )
        if demand["status"] == "unknown":
            reasons.append(MANUAL_REVIEW_HINT)
        else:
            reasons.append("Geprüfte Planliste ohne bekannten Eigenbedarf")
    if preference and preference.replenishment_unlikely:
        reasons.append("Manueller Hinweis: Nachschub unwahrscheinlich")
    return {
        "part_num": part_num,
        "color_id": color_id,
        "classification": classification,
        "history": history,
        "demand": demand,
        "manual_review": classification == "manual_archive_review",
        "hint": MANUAL_REVIEW_HINT
        if classification == "manual_archive_review"
        else None,
        "reasons": reasons,
        "missing": sorted(set(history["missing"] + demand["missing"])),
    }


def _unit_location_id(unit_id):
    """Resolve fixed location without treating an unplaced unit as an empty shelf."""
    visited = set()
    current = unit_id
    while current is not None and current not in visited:
        visited.add(current)
        unit = db.session.get(StorageUnit, current)
        if unit is None:
            return None
        if unit.host_unit_id is not None:
            current = unit.host_unit_id
            continue
        placement = db.session.get(StoragePlacement, current)
        if placement is None:
            return None
        if placement.shelf_id is not None:
            return placement.shelf_id
        current = placement.support_unit_id
    return None


def _within(location_id, ancestor_id):
    visited = set()
    while location_id is not None and location_id not in visited:
        if location_id == ancestor_id:
            return True
        visited.add(location_id)
        location = db.session.get(StorageLocation, location_id)
        location_id = location.parent_id if location else None
    return False


def _archive_location(location_id):
    visited = set()
    while location_id is not None and location_id not in visited:
        visited.add(location_id)
        location = db.session.get(StorageLocation, location_id)
        if location is None:
            return False
        if location.zone_kind == "archive":
            return True
        location_id = location.parent_id
    return False


def intake_suggestion(part_num, color_id, as_of=None):
    part = db.session.get(RebrickableParts, part_num)
    if part is None:
        raise NotFound("Part not found.")
    result = classify_variant(part_num, color_id, as_of)
    rule = CategoryStorageRule.query.filter_by(category_id=part.part_cat_id).first()
    default_id = rule.location_id if rule else None
    if (
        result["classification"] == "archive_candidate"
        and rule
        and rule.archive_location_id
    ):
        default_id = rule.archive_location_id
    existing = []
    for row in (
        PartStorage.query.filter_by(part_num=part_num, color_id=color_id)
        .order_by(PartStorage.id)
        .all()
    ):
        unit = (
            db.session.get(StorageUnit, row.storage_unit_id)
            if row.storage_unit_id
            else None
        )
        location_id = _unit_location_id(unit.id) if unit else None
        eligible = bool(unit and unit.fill_state == "space" and location_id is not None)
        if default_id is not None:
            eligible = eligible and _within(location_id, default_id)
        elif _archive_location(location_id):
            eligible = False
        existing.append(
            {
                "storage_id": row.id,
                "unit_id": row.storage_unit_id,
                "quantity": row.quantity,
                "location_id": location_id,
                "eligible": eligible,
                "fill_state": unit.fill_state if unit else "unknown",
            }
        )
    targets = [row for row in existing if row["eligible"]]
    result.update(
        {
            "default_location_id": default_id,
            "target_unit_id": targets[0]["unit_id"] if targets else None,
            "existing_locations": existing,
            "category_id": part.part_cat_id,
        }
    )
    if demand_unknown := result["demand"]["status"] == "unknown":
        result["reasons"].append(
            "Bei unbekanntem Eigenbedarf bleibt das Kategorieregal Standard"
        )
    if default_id is None:
        result["missing"].append("Kategorie-Standardort fehlt")
    elif not targets:
        result["reasons"].append(
            "Standardort – Fach/Behälter wählen und Kapazität prüfen"
        )
    result["intake_archive_default"] = (
        result["classification"] == "archive_candidate" and not demand_unknown
    )
    return result


def _contained_units(unit_id):
    """Host children move with their cabinet; supported containers do not."""
    found = set()
    pending = [unit_id]
    while pending:
        current = pending.pop()
        if current in found:
            continue
        found.add(current)
        pending.extend(
            r.id
            for r in StorageUnit.query.filter_by(
                host_unit_id=current, active=True
            ).all()
        )
    return found


def archive_suggestions(shelf_id, as_of=None):
    if db.session.get(StorageLocation, shelf_id) is None:
        raise NotFound("Storage location not found.")
    units = []
    classifications = {}
    for unit in StorageUnit.query.filter_by(active=True).order_by(StorageUnit.id).all():
        if not _within(_unit_location_id(unit.id), shelf_id):
            continue
        contents = []
        member_ids = _contained_units(unit.id)
        members = StorageUnit.query.filter(StorageUnit.id.in_(member_ids)).all()
        complete_contents = all(member.contents_complete for member in members)
        for row in (
            PartStorage.query.filter(PartStorage.storage_unit_id.in_(member_ids))
            .order_by(PartStorage.id)
            .all()
        ):
            if row.quantity == 0:
                continue
            key = row.part_num, row.color_id
            if key not in classifications:
                classifications[key] = classify_variant(*key, as_of)
            item = dict(classifications[key])
            item.update({"storage_id": row.id, "quantity": row.quantity})
            contents.append(item)
        eligible = [
            r["storage_id"]
            for r in contents
            if r["classification"] in {"manual_archive_review", "archive_candidate"}
        ]
        manual = any(
            r["manual_review"] for r in contents if r["storage_id"] in eligible
        )
        all_qualified = bool(contents) and len(eligible) == len(contents)
        supporters = [
            p.unit_id
            for p in StoragePlacement.query.filter_by(support_unit_id=unit.id).all()
        ]
        whole = bool(complete_contents and all_qualified and not supporters)
        reasons = []
        if not complete_contents:
            reasons.append("Behälterinhalt nicht vollständig aufgenommen")
        if not all_qualified and eligible:
            reasons.append("Gemischter/ungeprüfter Inhalt – Teilumbuchung prüfen")
        if supporters:
            reasons.append("Aufliegende Behälter zuerst gesondert umstellen")
        if whole:
            reasons.append(
                "Gesamten Behälter manuell auf Archivziel und Aufnahmefähigkeit prüfen"
            )
        placement = db.session.get(StoragePlacement, unit.id)
        targets = set()
        for item in contents:
            if item["storage_id"] in eligible:
                part = db.session.get(RebrickableParts, item["part_num"])
                rule = (
                    CategoryStorageRule.query.filter_by(
                        category_id=part.part_cat_id
                    ).first()
                    if part
                    else None
                )
                if rule and rule.archive_location_id:
                    targets.add(rule.archive_location_id)
        units.append(
            {
                "unit_id": unit.id,
                "label": unit.label,
                "whole_box": whole,
                "manual_review": manual,
                "hint": MANUAL_REVIEW_HINT if manual else None,
                "eligible_storage_ids": eligible,
                "contents": contents,
                "reasons": reasons,
                "executable": False,
                "archive_location_ids": sorted(targets),
                "supporting_unit_ids": supporters,
                "effects": {
                    "empty_container_releases_space": False,
                    "lower_stack_if_removed": bool(
                        placement and placement.support_unit_id and not supporters
                    ),
                    "base_area_if_removed": bool(
                        placement and placement.shelf_id and not supporters
                    ),
                    "contiguous_space_verified": False,
                },
                "capacity_check_required": True,
            }
        )
    return {
        "shelf_id": shelf_id,
        "units": units,
        "explanation": "Prüfvorschläge ändern weder Bestand noch aktuellen Fundort. Leere Behälter belegen weiter Stellfläche; zusammenhängende Fläche erst nach konkreter Umstellungsplanung prüfen.",
    }


def get_settings():
    categories = [
        {"id": category.id, "name": category.name}
        for category in RebrickablePartCategories.query.order_by(
            RebrickablePartCategories.name, RebrickablePartCategories.id
        ).all()
    ]
    category_names = {category["id"]: category["name"] for category in categories}
    return {
        **{key: rule_number(key, value) for key, value in DEFAULTS.items()},
        "planning_reviewed": _reviewed(),
        "categories": categories,
        "category_rules": [
            {
                "id": r.id,
                "category_id": r.category_id,
                "category_name": category_names.get(r.category_id),
                "location_id": r.location_id,
                "archive_location_id": r.archive_location_id,
            }
            for r in CategoryStorageRule.query.order_by(CategoryStorageRule.id).all()
        ],
        "preferences": [
            {
                "id": r.id,
                "part_num": r.part_num,
                "color_id": r.color_id,
                "keep_accessible": r.keep_accessible,
                "replenishment_unlikely": r.replenishment_unlikely,
            }
            for r in PartStoragePreference.query.order_by(
                PartStoragePreference.id
            ).all()
        ],
        "planned_sets": [
            {
                "id": r.id,
                "set_num": r.set_num,
                "quantity": r.quantity,
                "active": r.active,
                "revision": r.revision,
            }
            for r in PlannedSet.query.order_by(PlannedSet.id).all()
        ],
    }


def save_settings(data):
    data = _body(data)
    unknown = set(data) - set(DEFAULTS) - {"planning_reviewed"}
    if unknown:
        raise BadRequest("Unknown warehouse setting.")
    for key in DEFAULTS:
        if key in data:
            _integer(data[key], key, minimum=1)
    if "planning_reviewed" in data and not isinstance(data["planning_reviewed"], bool):
        raise BadRequest("planning_reviewed must be boolean.")
    for key in DEFAULTS:
        if key in data:
            _put_setting(key, data[key])
    if "planning_reviewed" in data:
        _put_setting(
            "planning_reviewed", "true" if data["planning_reviewed"] else "false"
        )
        _put_setting("planning_signature", _planning_signature())
    db.session.commit()
    return get_settings()


def save_category_rule(data):
    data = _body(data)
    category = _integer(data.get("category_id"), "category_id", minimum=1)
    location = _integer(data.get("location_id"), "location_id", minimum=1)
    archive = _integer(
        data.get("archive_location_id"), "archive_location_id", minimum=1, nullable=True
    )
    if db.session.get(RebrickablePartCategories, category) is None:
        raise NotFound("Category not found.")
    for location_id in (location, archive):
        if (
            location_id is not None
            and db.session.get(StorageLocation, location_id) is None
        ):
            raise NotFound("Storage location not found.")
    row = CategoryStorageRule.query.filter_by(category_id=category).first()
    if row is None:
        row = CategoryStorageRule()
        row.category_id = category
        db.session.add(row)
    else:
        row.revision += 1
    row.location_id, row.archive_location_id = location, archive
    db.session.commit()
    return {
        "id": row.id,
        "category_id": category,
        "location_id": location,
        "archive_location_id": archive,
    }


def save_preference(data):
    data = _body(data)
    part_num = data.get("part_num")
    if (
        not isinstance(part_num, str)
        or db.session.get(RebrickableParts, part_num) is None
    ):
        raise NotFound("Part not found.")
    color_id = _integer(data.get("color_id"), "color_id", nullable=True)
    if color_id is not None and db.session.get(RebrickableColors, color_id) is None:
        raise NotFound("Color not found.")
    keep = data.get("keep_accessible", False)
    replenish = data.get("replenishment_unlikely")
    if not isinstance(keep, bool) or (
        replenish is not None and not isinstance(replenish, bool)
    ):
        raise BadRequest("Preference flags must be boolean or null where supported.")
    row = PartStoragePreference.query.filter_by(
        part_num=part_num, color_id=color_id
    ).first()
    if row is None:
        row = PartStoragePreference()
        row.part_num = part_num
        row.color_id = color_id
        db.session.add(row)
    else:
        row.revision += 1
    row.keep_accessible, row.replenishment_unlikely = keep, replenish
    db.session.commit()
    return {
        "id": row.id,
        "part_num": part_num,
        "color_id": color_id,
        "keep_accessible": keep,
        "replenishment_unlikely": replenish,
    }


def _save_plan(row, data):
    set_num = data.get("set_num", row.set_num)
    quantity = _integer(data.get("quantity", row.quantity or 1), "quantity", minimum=1)
    active = data.get("active", True if row.active is None else row.active)
    if not isinstance(set_num, str) or db.session.get(RebrickableSets, set_num) is None:
        raise NotFound("Set not found.")
    if not isinstance(active, bool):
        raise BadRequest("active must be boolean.")
    if row.id is not None:
        row.revision += 1
    row.set_num, row.quantity, row.active = set_num, quantity, active
    db.session.add(row)
    _put_setting("planning_reviewed", "false")
    db.session.commit()
    return {
        "id": row.id,
        "set_num": row.set_num,
        "quantity": row.quantity,
        "active": row.active,
        "revision": row.revision,
    }


def save_planned_set(data):
    return _save_plan(PlannedSet(), _body(data))


def update_planned_set(plan_id, data):
    row = db.session.get(PlannedSet, plan_id)
    if row is None:
        raise NotFound("Planned set not found.")
    data = _body(data)
    return _save_plan(row, data)
