"""Historical Bricks occurrences and durable catalog provenance.

Observed catalog values are never substituted for unknown values. Inventories
are versioned sources; distinct real set numbers, rather than rows, are counted.
"""

from collections import defaultdict
from datetime import date, datetime

from models import (
    CatalogGeneration,
    ConfigSettings,
    RebrickableColors,
    RebrickableInventories,
    RebrickableInventoryMinifigs,
    RebrickableInventoryParts,
    RebrickableInventorySets,
    RebrickablePartRelationships,
    RebrickableParts,
    RebrickableSets,
    db,
)
from sqlalchemy import select, text

CATALOG_FILES = (
    "part_categories.csv.gz",
    "colors.csv.gz",
    "parts.csv.gz",
    "part_relationships.csv.gz",
    "elements.csv.gz",
    "themes.csv.gz",
    "sets.csv.gz",
    "minifigs.csv.gz",
    "inventories.csv.gz",
    "inventory_parts.csv.gz",
    "inventory_sets.csv.gz",
    "inventory_minifigs.csv.gz",
)


def _today(as_of=None):
    if isinstance(as_of, datetime):
        return as_of.date()
    return as_of or date.today()


def rule_number(key, default):
    """Read only a known, non-secret warehouse numeric preference."""
    setting = ConfigSettings.query.filter_by(
        key=f"warehouse.{key}", encrypted=False
    ).first()
    try:
        value = int(setting.value) if setting else default
    except (TypeError, ValueError):
        return default
    return value if value >= 0 else default


def catalog_status(as_of=None):
    """The latest attempt owns provenance, including partial/failed attempts."""
    generation = CatalogGeneration.query.order_by(CatalogGeneration.id.desc()).first()
    missing = []
    if generation is None:
        return {
            "generation_id": None,
            "revision": None,
            "complete": False,
            "missing": ["Katalogabdeckung nicht geprüft"],
        }
    if (
        generation.status != "completed"
        or CatalogGeneration.query.filter_by(status="running").first() is not None
    ):
        missing.append("Katalogimport läuft oder ist fehlgeschlagen")
    files = generation.files or {}
    if any(
        not isinstance(files.get(name), dict)
        or files[name].get("status") != "completed"
        or not isinstance(files[name].get("records"), int)
        for name in CATALOG_FILES
    ):
        missing.append("Katalogdateien nicht vollständig geprüft")
    if generation.errors:
        missing.append("Katalogverknüpfungen unvollständig")
    completed = generation.completed_at
    if completed is None:
        missing.append("Katalogabschluss unbekannt")
    elif (
        not 0
        <= (_today(as_of) - completed.date()).days
        <= rule_number("catalog_max_age_days", 90)
    ):
        missing.append("Kataloggeneration nicht aktuell")
    return {
        "generation_id": generation.id,
        "revision": generation.revision,
        "complete": not missing,
        "missing": missing,
    }


def _parent_inventories(entity):
    """An entity may be an actual set, a minifigure, or an orphan reference."""
    parents = set()
    for row in RebrickableInventorySets.query.filter_by(set_num=entity).all():
        if row.quantity > 0:
            parents.add(row.inventory_id)
    for row in RebrickableInventoryMinifigs.query.filter_by(fig_num=entity).all():
        if row.quantity > 0:
            parents.add(row.inventory_id)
    return parents


def _real_parent_sets(inventory_id):
    found = set()
    problems = set()
    visited = set()
    pending = [(inventory_id, frozenset())]
    while pending:
        current, path = pending.pop()
        if current in path:
            problems.add("Zyklus in Unterinventaren")
            continue
        if current in visited:
            continue
        visited.add(current)
        inventory = db.session.get(RebrickableInventories, current)
        if inventory is None:
            problems.add("Inventarverknüpfung fehlt")
            continue
        entity = inventory.set_num
        real_set = db.session.get(RebrickableSets, entity)
        parents = _parent_inventories(entity)
        if real_set is not None:
            found.add(real_set.set_num)
        elif not parents:
            problems.add("Set-Zuordnung fehlt")
        pending.extend((parent, path | {current}) for parent in parents)
    return found, problems


def part_history(part_num, color_id, as_of=None):
    """Return distinct observed set occurrences for an exact part/color pair."""
    today = _today(as_of)
    provenance = catalog_status(today)
    missing = set(provenance["missing"])
    part = db.session.get(RebrickableParts, part_num)
    if part is None:
        missing.add("Teilenummer im Katalog unbekannt")
    if color_id is None:
        missing.add("Farbe unbestimmt")
    elif db.session.get(RebrickableColors, color_id) is None:
        missing.add("Farbkennung im Katalog unbekannt")
    rows = (
        RebrickableInventoryParts.query.filter_by(part_num=part_num, color_id=color_id)
        .filter(RebrickableInventoryParts.quantity > 0)
        .all()
    )
    occurrences = defaultdict(set)
    for row in rows:
        real_sets, problems = _real_parent_sets(row.inventory_id)
        missing.update(problems)
        for set_num in real_sets:
            occurrences[set_num].add("spare" if row.is_spare else "regular")
    years = []
    sets = []
    for set_num in sorted(occurrences):
        item = db.session.get(RebrickableSets, set_num)
        year = item.year if item else None
        valid_year = isinstance(year, int) and 1900 <= year <= today.year + 1
        if valid_year:
            years.append(year)
        else:
            missing.add("Set-Jahr fehlt oder ist unplausibel")
        sets.append(
            {
                "set_num": set_num,
                "year": year if valid_year else None,
                "spare_only": occurrences[set_num] == {"spare"},
            }
        )
    if not sets:
        missing.add("Keine bekannten Set-Verknüpfungen")
    relationships = RebrickablePartRelationships.query.filter(
        (RebrickablePartRelationships.child_part_num == part_num)
        | (RebrickablePartRelationships.parent_part_num == part_num)
    ).all()
    return {
        "part_num": part_num,
        "color_id": color_id,
        "known_set_count": len(sets),
        "first_year": min(years) if years else None,
        "last_year": max(years) if years else None,
        "sets": sets,
        "spare_only": bool(sets) and all(s["spare_only"] for s in sets),
        "includes_spares": True,
        "complete": not missing,
        "missing": sorted(missing),
        "catalog": provenance,
        "computed_on": today.isoformat(),
        "related_parts": [
            {"parent": r.parent_part_num, "child": r.child_part_num, "type": r.rel_type}
            for r in relationships
        ],
    }


def catalog_validation_errors():
    """Validate cross-file references before publishing an import generation.

    Missing catalog data is retained and surfaced, never repaired by deleting
    user-owned records. Validation is performed once per import, not per part.
    """
    errors = []
    inv = {r.id: r.set_num for r in RebrickableInventories.query.all()}
    entities = set(inv.values())
    sets = {r.set_num for r in RebrickableSets.query.all()}
    if not sets or not inv:
        errors.append("sets_or_inventories_empty")
    for model in (
        RebrickableInventoryParts,
        RebrickableInventorySets,
        RebrickableInventoryMinifigs,
    ):
        if (
            db.session.query(model)
            .outerjoin(
                RebrickableInventories, model.inventory_id == RebrickableInventories.id
            )
            .filter(RebrickableInventories.id.is_(None))
            .first()
            is not None
        ):
            errors.append(f"{model.__tablename__}:missing_inventory")
    for row in RebrickableInventorySets.query.all():
        if row.quantity > 0 and row.set_num not in entities:
            errors.append("inventory_sets:missing_child_inventory")
            break
    for row in RebrickableInventoryMinifigs.query.all():
        if row.quantity > 0 and row.fig_num not in entities:
            errors.append("inventory_minifigs:missing_child_inventory")
            break
    for table in db.metadata.tables.values():
        if not table.name.startswith("rebrickable_"):
            continue
        for foreign_key in table.foreign_keys:
            source = foreign_key.parent
            target = foreign_key.column
            target_table = target.table.alias(f"target_{source.name}")
            target_column = target_table.c[target.name]
            missing_reference = (
                select(source)
                .select_from(table.outerjoin(target_table, source == target_column))
                .where(source.is_not(None), target_column.is_(None))
                .limit(1)
            )
            if db.session.execute(missing_reference).first() is not None:
                errors.append(f"{table.name}:{source.name}:missing_reference")
    return sorted(set(errors))


def start_catalog_generation(import_id):
    # Serialize publication against other local import starters on SQLite.
    db.session.execute(
        text(
            "UPDATE catalog_generations SET revision = revision WHERE status = 'running'"
        )
    )
    db.session.expire_all()
    running = CatalogGeneration.query.filter_by(status="running").all()
    for other in running:
        other.errors = sorted(set((other.errors or []) + ["overlapping_import"]))
        other.revision += 1
    generation = CatalogGeneration()
    generation.import_id = import_id
    generation.status = "running"
    generation.files = {}
    generation.errors = ["overlapping_import"] if running else []
    db.session.add(generation)
    db.session.commit()
    return generation.id


def record_catalog_file(generation_id, filename, records):
    generation = db.session.get(CatalogGeneration, generation_id)
    if generation is None:
        raise ValueError("Catalog generation does not exist.")
    files = dict(generation.files or {})
    files[filename] = {
        "status": "completed",
        "records": records,
        "source": f"cdn.rebrickable.com/media/downloads/{filename}",
    }
    generation.files = files
    generation.revision += 1
    db.session.commit()


def finish_catalog_generation(generation_id, *, failed=False):
    generation = db.session.get(CatalogGeneration, generation_id)
    if generation is None:
        raise ValueError("Catalog generation does not exist.")
    generation.status = "failed" if failed else "completed"
    generation.completed_at = datetime.now()
    generation.errors = sorted(
        set(
            (generation.errors or [])
            + (["import_failed"] if failed else catalog_validation_errors())
        )
    )
    generation.revision += 1
    db.session.commit()
