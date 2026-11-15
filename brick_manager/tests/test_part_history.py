"""Historical occurrence/provenance regressions using isolated catalog fixtures."""

from datetime import date, datetime, timedelta
from unittest.mock import Mock

import pytest
from models import (
    CatalogGeneration,
    RebrickableColors,
    RebrickableInventories,
    RebrickableInventoryMinifigs,
    RebrickableInventoryParts,
    RebrickableInventorySets,
    RebrickableMinifigs,
    RebrickablePartCategories,
    RebrickableParts,
    RebrickableSets,
    RebrickableThemes,
    db,
)
from routes import import_rebrickable_data as importer
from services.part_history_service import CATALOG_FILES, catalog_status, part_history

TODAY = date(2026, 11, 15)


def completed_catalog():
    row = CatalogGeneration(
        import_id="fixture-full",
        status="completed",
        completed_at=datetime(2026, 11, 15),
        files={name: {"status": "completed", "records": 1} for name in CATALOG_FILES},
        errors=[],
    )
    db.session.add(row)
    db.session.flush()
    return row


def catalog_fixture():
    db.session.add_all(
        [
            RebrickablePartCategories(id=1, name="Bricks"),
            RebrickableColors(id=1, name="Red", rgb="FF0000"),
            RebrickableColors(id=2, name="Blue", rgb="0000FF"),
            RebrickableThemes(id=1, name="Test"),
        ]
    )
    db.session.flush()
    db.session.add_all(
        [
            RebrickableParts(part_num="old", name="Old Bricks", part_cat_id=1),
            RebrickableParts(part_num="new", name="New Bricks", part_cat_id=1),
            RebrickableSets(
                set_num="old-set", name="Old", year=2014, theme_id=1, num_parts=2
            ),
            RebrickableSets(
                set_num="new-set", name="New", year=2025, theme_id=1, num_parts=2
            ),
        ]
    )
    db.session.flush()
    db.session.add_all(
        [
            RebrickableInventories(id=1, set_num="old-set", version=1),
            RebrickableInventories(id=2, set_num="old-set", version=2),
            RebrickableInventories(id=3, set_num="new-set", version=1),
        ]
    )
    db.session.flush()
    db.session.add_all(
        [
            RebrickableInventoryParts(
                inventory_id=1, part_num="old", color_id=1, quantity=5, is_spare=False
            ),
            RebrickableInventoryParts(
                inventory_id=1, part_num="old", color_id=1, quantity=1, is_spare=True
            ),
            RebrickableInventoryParts(
                inventory_id=2, part_num="old", color_id=1, quantity=3, is_spare=False
            ),
            RebrickableInventoryParts(
                inventory_id=3, part_num="new", color_id=1, quantity=2, is_spare=False
            ),
        ]
    )
    completed_catalog()
    db.session.commit()


@pytest.fixture
def catalog(app):
    catalog_fixture()


def test_distinct_sets_not_inventory_versions_quantities_or_spares(catalog):
    result = part_history("old", 1, TODAY)
    assert result["known_set_count"] == 1
    assert result["first_year"] == result["last_year"] == 2014
    assert result["complete"] is True
    assert result["sets"] == [{"set_num": "old-set", "year": 2014, "spare_only": False}]
    assert part_history("old", 2, TODAY)["known_set_count"] == 0
    assert part_history("old", None, TODAY)["last_year"] is None


def test_minifigure_and_subsets_resolve_real_parents_once(catalog):
    db.session.add(RebrickableMinifigs(fig_num="fig-x", name="Figure", num_parts=1))
    db.session.add_all(
        [
            RebrickableInventories(id=4, set_num="fig-x", version=1),
            RebrickableInventoryMinifigs(inventory_id=2, fig_num="fig-x", quantity=2),
            RebrickableInventorySets(inventory_id=3, set_num="old-set", quantity=3),
        ]
    )
    db.session.flush()
    db.session.add(
        RebrickableInventoryParts(
            inventory_id=4, part_num="old", color_id=1, quantity=8, is_spare=False
        )
    )
    db.session.commit()
    result = part_history("old", 1, TODAY)
    assert result["known_set_count"] == 2
    assert {r["set_num"] for r in result["sets"]} == {"old-set", "new-set"}
    assert result["last_year"] == 2025
    assert result["complete"] is True


def test_unresolved_inventory_is_unknown_not_zero_or_current(catalog):
    db.session.add(RebrickableInventories(id=4, set_num="unknown-parent", version=1))
    db.session.flush()
    db.session.add(
        RebrickableInventoryParts(
            inventory_id=4, part_num="old", color_id=1, quantity=1, is_spare=False
        )
    )
    db.session.commit()
    result = part_history("old", 1, TODAY)
    assert result["known_set_count"] == 1
    assert result["complete"] is False
    assert "Set-Zuordnung fehlt" in result["missing"]


def test_missing_year_does_not_disappear_in_join(catalog):
    db.session.get(RebrickableSets, "old-set").year = 0
    db.session.commit()
    result = part_history("old", 1, TODAY)
    assert result["known_set_count"] == 1
    assert result["first_year"] is None and result["last_year"] is None
    assert result["complete"] is False
    assert "Set-Jahr fehlt oder ist unplausibel" in result["missing"]


def test_cycle_is_explained_without_unbounded_recursion(catalog):
    db.session.add_all(
        [
            RebrickableInventorySets(inventory_id=3, set_num="old-set", quantity=1),
            RebrickableInventorySets(inventory_id=2, set_num="new-set", quantity=1),
        ]
    )
    db.session.commit()
    result = part_history("old", 1, TODAY)
    assert result["known_set_count"] == 2
    assert "Zyklus in Unterinventaren" in result["missing"]


def test_latest_failed_partial_and_stale_generations_invalidate_old_confidence(catalog):
    assert catalog_status(TODAY)["complete"] is True
    generation = CatalogGeneration(
        import_id="failed", status="failed", files={}, errors=["failed"]
    )
    db.session.add(generation)
    db.session.commit()
    assert part_history("old", 1, TODAY)["complete"] is False
    generation.status = "completed"
    generation.completed_at = datetime(2026, 11, 15) - timedelta(days=100)
    generation.files = {
        name: {"status": "completed", "records": 1} for name in CATALOG_FILES
    }
    generation.errors = []
    db.session.commit()
    assert "Kataloggeneration nicht aktuell" in part_history("old", 1, TODAY)["missing"]


def test_regular_import_route_persists_failed_attempt_and_keeps_catalog(
    catalog, client, monkeypatch
):
    monkeypatch.setattr(
        importer, "download_and_extract_csv", Mock(side_effect=RuntimeError("private"))
    )
    result = client.post("/import_data")
    assert result.status_code == 500
    assert b"private" not in result.data
    latest = CatalogGeneration.query.order_by(CatalogGeneration.id.desc()).first()
    assert latest.status == "failed"
    assert db.session.get(RebrickableSets, "old-set").year == 2014
    assert part_history("old", 1, TODAY)["complete"] is False


def test_regular_import_route_publishes_complete_file_manifest(
    catalog, client, monkeypatch
):
    monkeypatch.setattr(
        importer, "download_and_extract_csv", Mock(side_effect=lambda name: name)
    )
    monkeypatch.setattr(importer, "import_csv_to_sqlite", Mock(return_value=4))
    result = client.post("/import_data")
    assert result.status_code == 200
    latest = CatalogGeneration.query.order_by(CatalogGeneration.id.desc()).first()
    assert latest.status == "completed"
    assert set(latest.files) == set(CATALOG_FILES)
    assert all(v["records"] == 4 for v in latest.files.values())
    assert latest.errors == []


def test_overlapping_imports_remain_untrusted_after_both_finish(catalog):
    from services.part_history_service import (
        finish_catalog_generation,
        record_catalog_file,
        start_catalog_generation,
    )

    first = start_catalog_generation("first-overlap")
    second = start_catalog_generation("second-overlap")
    for generation in (first, second):
        for filename in CATALOG_FILES:
            record_catalog_file(generation, filename, 1)
        finish_catalog_generation(generation)
    latest = db.session.get(CatalogGeneration, second)
    assert "overlapping_import" in latest.errors
    assert catalog_status(TODAY)["complete"] is False
