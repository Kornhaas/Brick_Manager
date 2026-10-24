"""Migration contract for durable dashboard history."""

import sqlite3
from pathlib import Path


def test_collection_snapshot_migration_is_repeatable():
    migration = (
        Path(__file__).parents[1]
        / "migrations"
        / "20261023_add_collection_snapshots.sql"
    ).read_text(encoding="utf-8")
    connection = sqlite3.connect(":memory:")

    connection.executescript(migration)
    connection.executescript(migration)

    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(collection_snapshots)")
    }
    assert columns == {
        "id",
        "captured_on",
        "total_sets",
        "owned_parts",
        "required_parts",
        "missing_parts",
        "complete_sets",
        "incomplete_sets",
    }
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
