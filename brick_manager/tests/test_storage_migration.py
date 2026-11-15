"""Physical-storage migrations preserve legacy data and recover atomically."""

import hashlib
import sqlite3
from pathlib import Path

import pytest
from models import PartStorage, StorageLocation, db
from services.migration_service import (
    apply_sqlite_migrations,
    backup_sqlite_database,
    inspect_storage_database,
    main,
)
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.sqlite import dialect
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

MIGRATIONS = Path(__file__).parents[1] / "migrations"


def _old_database(path, *, with_quantity=False):
    connection = sqlite3.connect(path)
    for table in db.metadata.sorted_tables:
        if table.name.startswith(("rebrickable_", "user_")):
            connection.execute(str(CreateTable(table).compile(dialect=dialect())))
    quantity_column = ", quantity INTEGER" if with_quantity else ""
    connection.execute(
        "CREATE TABLE part_storage (id INTEGER PRIMARY KEY, "
        "part_num TEXT NOT NULL REFERENCES rebrickable_parts(part_num), "
        "color_id INTEGER REFERENCES rebrickable_colors(id), location TEXT, "
        "level TEXT, box TEXT, notes TEXT, label_printed BOOLEAN NOT NULL DEFAULT 0"
        f"{quantity_column})"
    )
    connection.execute("INSERT INTO rebrickable_part_categories VALUES (1, 'Bricks')")
    connection.execute(
        "INSERT INTO rebrickable_parts (part_num, name, part_cat_id) VALUES ('p', 'Part', 1)"
    )
    connection.execute(
        "INSERT INTO rebrickable_colors (id, name, rgb, is_trans) VALUES (1, 'Red', 'FF0000', 0)"
    )
    connection.execute("INSERT INTO rebrickable_themes (id, name) VALUES (1, 'Theme')")
    connection.execute(
        "INSERT INTO rebrickable_sets (set_num, name, year, theme_id, num_parts) "
        "VALUES ('s-1', 'Set', 2000, 1, 10)"
    )
    connection.execute(
        "INSERT INTO user_sets (id, set_num, status, label_printed) VALUES (1, 's-1', 'unknown', 1)"
    )
    connection.execute(
        "INSERT INTO user_parts (id, part_num, color_id, quantity, have_quantity, "
        "user_set_id, is_spare) VALUES (1, 'p', 1, 10, 7, 1, 0)"
    )
    rows = [
        (41, "p", 1, " 01 ", "05", "6", "keep exactly", 1),
        (42, "p", None, " 01 ", "05", "6", "another physical box?", 0),
        (49, "p", None, None, "", "9", "unknown location", 1),
    ]
    for row in rows:
        connection.execute(
            "INSERT INTO part_storage "
            "(id, part_num, color_id, location, level, box, notes, label_printed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            row,
        )
    if with_quantity:
        connection.execute("UPDATE part_storage SET quantity = 8 WHERE id = 41")
    connection.commit()
    connection.close()
    return rows


def test_fresh_database_migrates_and_works_through_sqlalchemy(tmp_path):
    path = tmp_path / "fresh.db"
    assert apply_sqlite_migrations(path, MIGRATIONS) == []
    assert apply_sqlite_migrations(path, MIGRATIONS) == []
    engine = create_engine(f"sqlite:///{path}")
    with Session(engine) as session:
        session.add(StorageLocation(kind="zone", label="Test area"))
        session.commit()
        assert session.scalar(select(StorageLocation.label)) == "Test area"
    engine.dispose()
    with sqlite3.connect(path) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            == 3
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_old_rows_labels_counts_and_unknowns_are_preserved(tmp_path):
    path = tmp_path / "legacy.db"
    expected = _old_database(path)
    before = inspect_storage_database(path)
    assert before["storage_rows"] == 3
    assert before["incomplete_locations"] == 1
    assert before["repeated_location_groups"] == 1
    assert before["unresolved_colours"] == 2
    backup = backup_sqlite_database(path, tmp_path / "backup.db")
    assert apply_sqlite_migrations(path, MIGRATIONS) == []
    assert apply_sqlite_migrations(path, MIGRATIONS) == []
    with sqlite3.connect(path) as connection:
        assert (
            connection.execute(
                "SELECT id, part_num, color_id, location, level, box, notes, label_printed "
                "FROM part_storage ORDER BY id"
            ).fetchall()
            == expected
        )
        assert connection.execute(
            "SELECT quantity, have_quantity FROM user_parts"
        ).fetchall() == [(10, 7)]
        assert (
            connection.execute(
                "SELECT quantity, storage_unit_id FROM part_storage"
            ).fetchall()
            == [(None, None)] * 3
        )
        assert (
            connection.execute("SELECT COUNT(*) FROM storage_units").fetchone()[0] == 0
        )
        mappings = connection.execute(
            "SELECT storage_id, candidate_key, confirmed FROM legacy_storage_mappings ORDER BY storage_id"
        ).fetchall()
        assert [row[0] for row in mappings] == [41, 42, 49]
        assert mappings[0][1] == mappings[1][1]
        assert all(row[2] == 0 for row in mappings)
        assert connection.execute(
            "SELECT label FROM storage_locations WHERE kind = 'rack'"
        ).fetchall() == [(" 01 ",)]
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    # Backup is the exact recovery target, not an implicit automatic restore.
    with sqlite3.connect(backup) as connection:
        assert (
            connection.execute(
                "SELECT id, part_num, color_id, location, level, box, notes, label_printed "
                "FROM part_storage ORDER BY id"
            ).fetchall()
            == expected
        )
        assert "quantity" not in {
            row[1] for row in connection.execute("PRAGMA table_info(part_storage)")
        }
    engine = create_engine(f"sqlite:///{path}")
    with Session(engine) as session:
        stored = session.get(PartStorage, 41)
        assert stored.quantity is None
        assert stored.notes == "keep exactly"
        stored.quantity = 8
        session.commit()
        assert session.get(PartStorage, 41).quantity == 8
    engine.dispose()


def test_existing_physical_count_is_not_overwritten(tmp_path):
    path = tmp_path / "counted.db"
    _old_database(path, with_quantity=True)
    apply_sqlite_migrations(path, MIGRATIONS)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT quantity FROM part_storage ORDER BY id"
        ).fetchall() == [(8,), (None,), (None,)]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE part_storage SET revision=0 WHERE id=41")


def test_interrupted_migration_rolls_back_schema_backfill_and_journal(tmp_path):
    path = tmp_path / "failed.db"
    _old_database(path)
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_failing.sql").write_text(
        "ALTER TABLE part_storage ADD COLUMN accidental TEXT;\n"
        "UPDATE part_storage SET box = 'overwritten';\n"
        "INSERT INTO missing_table VALUES (1);\n"
    )
    with pytest.raises(sqlite3.OperationalError):
        apply_sqlite_migrations(path, migrations)
    with sqlite3.connect(path) as connection:
        assert "accidental" not in {
            row[1] for row in connection.execute("PRAGMA table_info(part_storage)")
        }
        assert connection.execute(
            "SELECT box FROM part_storage WHERE id=41"
        ).fetchone() == ("6",)
        assert (
            connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            == 0
        )
    (migrations / "001_failing.sql").write_text(
        "ALTER TABLE part_storage ADD COLUMN recovered TEXT;\n"
    )
    apply_sqlite_migrations(path, migrations)
    apply_sqlite_migrations(path, migrations)
    with sqlite3.connect(path) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            == 1
        )


def test_applied_artifact_cannot_change_silently(tmp_path):
    path = tmp_path / "hash.db"
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    artifact = migrations / "001_table.sql"
    artifact.write_text("CREATE TABLE kept (id INTEGER PRIMARY KEY);\n")
    apply_sqlite_migrations(path, migrations)
    original_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.write_text("DROP TABLE kept;\n")
    with pytest.raises(ValueError, match="Applied migration changed"):
        apply_sqlite_migrations(path, migrations)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT checksum FROM schema_migrations"
        ).fetchone() == (original_hash,)
        assert connection.execute("SELECT COUNT(*) FROM kept").fetchone() == (0,)


def test_new_foreign_key_damage_rolls_back_but_legacy_damage_remains(tmp_path):
    path = tmp_path / "foreign.db"
    _old_database(path)
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_damage.py").write_text(
        "def upgrade(connection):\n"
        "    connection.execute('PRAGMA defer_foreign_keys = ON')\n"
        "    connection.execute(\"UPDATE part_storage SET part_num='not-a-part' WHERE id=41\")\n"
    )
    with pytest.raises(ValueError, match="introduced foreign-key violations"):
        apply_sqlite_migrations(path, migrations)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT part_num FROM part_storage WHERE id=41"
        ).fetchone() == ("p",)


def test_inspection_is_read_only_and_cli_reports_counts(tmp_path, capsys):
    path = tmp_path / "inspect.db"
    _old_database(path)
    before = path.read_bytes()
    main([str(path), "--inspect"])
    assert '"storage_rows": 3' in capsys.readouterr().out
    assert path.read_bytes() == before
    with pytest.raises(sqlite3.OperationalError):
        inspect_storage_database(tmp_path / "does-not-exist.db")
    assert not (tmp_path / "does-not-exist.db").exists()
    backup_sqlite_database(path, tmp_path / "backup.db")
    with pytest.raises(FileExistsError):
        backup_sqlite_database(path, tmp_path / "backup.db")


def test_backup_only_cli_does_not_migrate_selected_database(tmp_path):
    from services.migration_service import main

    source = tmp_path / "before.db"
    expected = _old_database(source)
    target = tmp_path / "backup.db"
    main([str(source), "--backup", str(target)])
    for database in (source, target):
        with sqlite3.connect(database) as connection:
            assert (
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE name='schema_migrations'"
                ).fetchone()
                is None
            )
            assert "storage_unit_id" not in {
                row[1] for row in connection.execute("PRAGMA table_info(part_storage)")
            }
    assert expected


@pytest.mark.parametrize("relative", [False, True])
def test_migration_prepares_actual_sqlite_parent_resolved_by_flask(tmp_path, relative):
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    instance = tmp_path / "flask-instance"
    selected = tmp_path / "selected storage" / "nested" / "collection.db"
    uri = (
        "sqlite:///data/instance/collection.db" if relative else f"sqlite:///{selected}"
    )
    application = Flask("storage-startup-contract", instance_path=str(instance))
    application.config["SQLALCHEMY_DATABASE_URI"] = uri
    database = SQLAlchemy(application)
    with application.app_context():
        engine = database.engine
        actual = Path(engine.url.database)
        assert not actual.parent.exists()
        assert apply_sqlite_migrations(actual, MIGRATIONS) == []
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO storage_locations (kind, label) VALUES ('zone', 'Kept collection')"
            )
        assert apply_sqlite_migrations(actual, MIGRATIONS) == []
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT label FROM storage_locations"
                ).scalar_one()
                == "Kept collection"
            )
        assert actual.is_file()
        assert actual == (
            instance / "data" / "instance" / "collection.db" if relative else selected
        )
        engine.dispose()


def test_inventory_image_index_is_repeatable_and_preserves_existing_rows(tmp_path):
    path = tmp_path / "image-index.db"
    _old_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO rebrickable_inventories (id, version, set_num) VALUES (1, 1, 's-1')"
        )
        connection.execute(
            "INSERT INTO rebrickable_inventory_parts (inventory_id, part_num, color_id, quantity, is_spare, img_url) VALUES (1, 'p', 1, 3, 0, 'https://example.test/p.png')"
        )
        before = connection.execute(
            "SELECT * FROM rebrickable_inventory_parts"
        ).fetchall()
        storage_before = connection.execute("SELECT * FROM part_storage").fetchall()
    migrations = tmp_path / "index-migrations"
    migrations.mkdir()
    artifact = MIGRATIONS / "20261115_warehouse_image_lookup.sql"
    (migrations / artifact.name).write_bytes(artifact.read_bytes())
    apply_sqlite_migrations(path, migrations)
    apply_sqlite_migrations(path, migrations)
    with sqlite3.connect(path) as connection:
        assert (
            connection.execute("SELECT * FROM rebrickable_inventory_parts").fetchall()
            == before
        )
        assert (
            connection.execute("SELECT * FROM part_storage").fetchall()
            == storage_before
        )
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT min(img_url) FROM rebrickable_inventory_parts WHERE part_num='p' AND color_id=1"
        ).fetchall()
        assert any(
            "ix_inventory_part_color_image" in str(row) and "COVERING" in str(row)
            for row in plan
        ), plan
        assert (
            connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            == 1
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
