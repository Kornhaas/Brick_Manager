"""Apply the repository's restart-safe SQLite schema migrations."""

import sqlite3
from pathlib import Path


def apply_sqlite_migrations(database_path, migrations_path):
    """Apply each SQL migration in name order and verify foreign keys.

    The project stores repeatable SQLite migrations as ``*.sql`` files rather
    than as an Alembic repository.  Existing collection data is never reset.
    """
    database = Path(database_path)
    migrations = sorted(Path(migrations_path).glob("*.sql"))

    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in migrations:
            connection.executescript(migration.read_text(encoding="utf-8"))
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key validation failed: {violations!r}")
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    import sys

    apply_sqlite_migrations(sys.argv[1], sys.argv[2])
