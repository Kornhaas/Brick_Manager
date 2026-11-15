"""Consistent file-backed SQLite snapshots and scoped scheduled-backup retention."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import Engine

from services.migration_service import backup_sqlite_database

_BACKUP_NAME = re.compile(
    r"brick_manager_\d{8}_\d{6}(?:_\d{6}_[0-9a-f]{32})?\.backup\.db"
)


def create_database_backup(
    engine: Engine, *, now: datetime | None = None
) -> Path | None:
    """Back up the engine's actual SQLite file; memory/other engines have no file."""
    if engine.dialect.name != "sqlite":
        return None
    database = engine.url.database
    if (
        not database
        or database == ":memory:"
        or database.startswith("file::memory:")
        or engine.url.query.get("mode") == "memory"
    ):
        return None
    source = Path(database)
    if not source.is_file():
        raise FileNotFoundError("Configured SQLite database does not exist")
    directory = source.parent / "backups"
    directory.mkdir(parents=True, exist_ok=True)
    instant = now or datetime.now()
    # UUID plus exclusive creation prevents overwriting a recovery point, even
    # when multiple processes schedule a backup within the same microsecond.
    name = f"brick_manager_{instant:%Y%m%d_%H%M%S_%f}_{uuid4().hex}.backup.db"
    return backup_sqlite_database(source, directory / name)


def prune_database_backups(
    directory: str | Path,
    *,
    now: datetime | None = None,
    retention_days: int = 7,
) -> list[Path]:
    """Remove only old files owned by the scheduled-backup naming contract."""
    cutoff = ((now or datetime.now()) - timedelta(days=retention_days)).timestamp()
    removed = []
    for path in Path(directory).iterdir():
        if (
            not _BACKUP_NAME.fullmatch(path.name)
            or path.is_symlink()
            or not path.is_file()
        ):
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
                removed.append(path)
        except FileNotFoundError:
            # Another backup process may have pruned the same old snapshot.
            continue
    return removed
