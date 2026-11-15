"""Versioned, transactional SQLite migrations and read-only storage inspection."""

import argparse
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path


def _execute_sql(connection, script):
    """Execute complete statements without executescript's implicit commits."""
    statement = ""
    for line in script.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise ValueError("Migration ends with incomplete SQL")


def _foreign_key_violations(connection):
    return connection.execute("PRAGMA foreign_key_check").fetchall()


def _read_only_connection(database_path):
    return sqlite3.connect(
        Path(database_path).resolve().as_uri() + "?mode=ro", uri=True
    )


def inspect_storage_database(database_path):
    """Return counts and ambiguity metrics without changing or creating a database."""
    connection = _read_only_connection(database_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        report = {
            "storage_rows": 0,
            "incomplete_locations": 0,
            "repeated_location_groups": 0,
            "unresolved_colours": 0,
            "known_quantities": 0,
            "mapped_units": 0,
            "foreign_key_violations": len(_foreign_key_violations(connection)),
            "migrations": [],
        }
        if "part_storage" in tables:
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(part_storage)")
            }
            rows = connection.execute(
                "SELECT location, level, box, color_id FROM part_storage"
            ).fetchall()
            report["storage_rows"] = len(rows)
            report["incomplete_locations"] = sum(
                not all(isinstance(value, str) and value.strip() for value in row[:3])
                for row in rows
            )
            report["unresolved_colours"] = sum(row[3] is None for row in rows)
            groups = {}
            for row in rows:
                key = tuple(row[:3])
                groups[key] = groups.get(key, 0) + 1
            report["repeated_location_groups"] = sum(
                count > 1 for count in groups.values()
            )
            if "quantity" in columns:
                report["known_quantities"] = connection.execute(
                    "SELECT COUNT(*) FROM part_storage WHERE quantity IS NOT NULL"
                ).fetchone()[0]
            if "storage_unit_id" in columns:
                report["mapped_units"] = connection.execute(
                    "SELECT COUNT(*) FROM part_storage WHERE storage_unit_id IS NOT NULL"
                ).fetchone()[0]
        if "schema_migrations" in tables:
            report["migrations"] = [
                row[0]
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
        return report
    finally:
        connection.close()


def backup_sqlite_database(database_path, backup_path):
    """Create a consistent backup at a new explicit path, never overwrite one."""
    target = Path(backup_path)
    source = _read_only_connection(database_path)
    try:
        # Exclusive creation avoids replacing an existing recovery point.
        with target.open("xb"):
            pass
        try:
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
            finally:
                destination.close()
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    finally:
        source.close()
    return target


def apply_sqlite_migrations(database_path, migrations_path):
    """Apply ordered SQL/Python artifacts once, checking hashes and FK deltas.

    Each artifact (including its backfill and journal record) is atomic. Existing
    catalog FK violations remain visible; a migration may not introduce new ones.
    No application import, scheduler, network call or collection reset is involved.
    """
    database = Path(database_path)
    migrations = sorted(
        path
        for path in Path(migrations_path).iterdir()
        if path.suffix in {".sql", ".py"} and not path.name.startswith("_")
    )
    # Flask-SQLAlchemy resolves relative SQLite URLs under instance_path, but
    # only creates that base directory. Prepare any configured nested parents
    # before the migration connection opens exactly the same database file.
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, checksum TEXT NOT NULL, "
            "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.commit()
        for migration in migrations:
            checksum = hashlib.sha256(migration.read_bytes()).hexdigest()
            connection.execute("BEGIN IMMEDIATE")
            try:
                applied = connection.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = ?",
                    (migration.name,),
                ).fetchone()
                if applied:
                    if applied[0] != checksum:
                        raise ValueError(
                            f"Applied migration changed: {migration.name}; "
                            "restore its original artifact and add a new migration"
                        )
                    connection.commit()
                    continue
                before = set(_foreign_key_violations(connection))
                if migration.suffix == ".sql":
                    _execute_sql(connection, migration.read_text(encoding="utf-8"))
                else:
                    spec = importlib.util.spec_from_file_location(
                        "_brick_storage_migration", migration
                    )
                    if spec is None or spec.loader is None:
                        raise ValueError("Cannot load migration artifact")
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    module.upgrade(connection)
                after = set(_foreign_key_violations(connection))
                if after - before:
                    raise ValueError("Migration introduced foreign-key violations")
                connection.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (?, ?)",
                    (migration.name, checksum),
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        violations = _foreign_key_violations(connection)
        if violations:
            print(
                "Warning: migration completed, but "
                f"{len(violations)} pre-existing foreign-key violation(s) remain.",
                file=sys.stderr,
            )
        return violations
    finally:
        connection.close()


def main(argv=None):
    """Inspect, explicitly back up, or migrate a selected development database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    parser.add_argument("migrations", nargs="?")
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--backup")
    args = parser.parse_args(argv)
    if args.inspect:
        print(json.dumps(inspect_storage_database(args.database), indent=2))
        return
    if args.backup:
        backup_sqlite_database(args.database, args.backup)
        if not args.migrations:
            return
    if not args.migrations:
        parser.error("migrations directory, --inspect or --backup is required")
    apply_sqlite_migrations(args.database, args.migrations)


if __name__ == "__main__":
    main()
