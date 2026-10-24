"""Regression tests for SQLite migration application in the container."""

import sqlite3
from pathlib import Path

from services.migration_service import apply_sqlite_migrations


def test_sqlite_migrations_preserve_existing_data_and_are_repeatable(tmp_path):
    database_path = tmp_path / "collection.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        "CREATE TABLE existing_collection (id INTEGER PRIMARY KEY, name TEXT)"
    )
    connection.execute("INSERT INTO existing_collection (name) VALUES ('Kept set')")
    connection.commit()
    connection.close()

    migrations_path = Path(__file__).parents[1] / "migrations"
    apply_sqlite_migrations(database_path, migrations_path)
    apply_sqlite_migrations(database_path, migrations_path)

    connection = sqlite3.connect(database_path)
    assert connection.execute("SELECT name FROM existing_collection").fetchone() == (
        "Kept set",
    )
    assert connection.execute("PRAGMA table_info(collection_snapshots)").fetchall()
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    connection.close()
