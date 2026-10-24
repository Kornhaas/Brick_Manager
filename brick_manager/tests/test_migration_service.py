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


def test_sqlite_migrations_do_not_block_on_legacy_catalog_foreign_keys(tmp_path):
    database_path = tmp_path / "collection.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE rebrickable_parts (part_num TEXT PRIMARY KEY);
        CREATE TABLE user_parts (
            id INTEGER PRIMARY KEY,
            part_num TEXT NOT NULL REFERENCES rebrickable_parts(part_num)
        );
        INSERT INTO user_parts (part_num) VALUES ('missing-catalog-part');
        """
    )
    connection.commit()
    connection.close()

    migrations_path = Path(__file__).parents[1] / "migrations"
    violations = apply_sqlite_migrations(database_path, migrations_path)

    assert violations == [("user_parts", 1, "rebrickable_parts", 0)]
    connection = sqlite3.connect(database_path)
    assert connection.execute("SELECT part_num FROM user_parts").fetchone() == (
        "missing-catalog-part",
    )
    assert connection.execute("PRAGMA table_info(collection_snapshots)").fetchall()
    connection.close()
