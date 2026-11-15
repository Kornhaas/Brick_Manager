"""Scheduled backups use real SQLite snapshots without importing the live app."""

import ast
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask
from models import db
from sqlalchemy import create_engine

APP_SOURCE = Path(__file__).parents[1] / "app.py"


def scheduler_functions(app):
    """Load only the scheduler wrappers, never app creation or startup jobs."""
    source = ast.parse(APP_SOURCE.read_text())
    functions = [
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"backup_database", "cleanup_old_backups"}
    ]
    namespace = {
        "app": app,
        "db": db,
        "os": os,
        "shutil": shutil,
        "datetime": datetime,
        "timedelta": timedelta,
    }
    exec(
        compile(ast.Module(body=functions, type_ignores=[]), str(APP_SOURCE), "exec"),
        namespace,
    )
    return namespace


def backup_app(tmp_path, uri):
    app = Flask("isolated-backup", instance_path=str(tmp_path / "instance"))
    app.config.update(SQLALCHEMY_DATABASE_URI=uri, SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    return app


def seed(path, value="kept"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE collection (value TEXT)")
        connection.execute("INSERT INTO collection VALUES (?)", (value,))


def values(path):
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return connection.execute(
            "SELECT value FROM collection ORDER BY rowid"
        ).fetchall()


def test_scheduled_backup_preserves_committed_wal_rows(tmp_path):
    source = tmp_path / "source.db"
    writer = sqlite3.connect(source)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE collection (value TEXT)")
    writer.execute("INSERT INTO collection VALUES ('committed in WAL')")
    writer.commit()
    assert Path(str(source) + "-wal").stat().st_size > 0
    writer.execute("INSERT INTO collection VALUES ('not committed')")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    old = backup_dir / "brick_manager_20000101_010101.backup.db"
    old.write_text("expired scheduled backup")
    expired = (datetime.now() - timedelta(days=8)).timestamp()
    os.utime(old, (expired, expired))
    app = backup_app(tmp_path, f"sqlite:///{source}")
    try:
        scheduler_functions(app)["backup_database"]()
        backups = list((tmp_path / "backups").glob("*.backup.db"))
        assert len(backups) == 1
        assert values(backups[0]) == [("committed in WAL",)]
        assert writer.execute("SELECT value FROM collection").fetchall() == [
            ("committed in WAL",),
            ("not committed",),
        ]
        assert not old.exists()
        writer.rollback()
    finally:
        writer.close()
        with app.app_context():
            db.engine.dispose()


def test_scheduled_backup_uses_flask_resolved_relative_database(tmp_path, monkeypatch):
    source = tmp_path / "instance" / "collection.db"
    decoy = tmp_path / "decoy" / "collection.db"
    seed(source, "real collection")
    seed(decoy, "wrong working-directory collection")
    monkeypatch.chdir(decoy.parent)
    app = backup_app(tmp_path, "sqlite:///collection.db")
    try:
        scheduler_functions(app)["backup_database"]()
        backups = list((source.parent / "backups").glob("*.backup.db"))
        assert len(backups) == 1
        assert values(backups[0]) == [("real collection",)]
        assert not (decoy.parent / "backups").exists()
    finally:
        with app.app_context():
            db.engine.dispose()


def test_rotation_preserves_unrelated_files_and_symlinks(tmp_path):
    old = tmp_path / "brick_manager_20000101_010101.backup.db"
    unrelated = tmp_path / "another_collection.backup.db"
    manual = tmp_path / "brick_manager-before-migration.backup.db"
    new = tmp_path / "brick_manager_20990101_010101.backup.db"
    for path in [old, unrelated, manual, new]:
        path.write_text("test backup")
    timestamp = (datetime.now() - timedelta(days=8)).timestamp()
    for path in [old, unrelated, manual]:
        os.utime(path, (timestamp, timestamp))
    link = tmp_path / "brick_manager_20000101_010102.backup.db"
    link.symlink_to(unrelated)
    namespace = scheduler_functions(SimpleNamespace(logger=Mock()))
    namespace["cleanup_old_backups"](tmp_path)
    assert not old.exists()
    assert unrelated.exists() and manual.exists() and new.exists()
    assert link.is_symlink()


def test_successive_backups_in_same_instant_are_distinct(tmp_path):
    from services.backup_service import create_database_backup

    source = tmp_path / "source.db"
    seed(source)
    engine = create_engine(f"sqlite:///{source}")
    try:
        instant = datetime(2026, 11, 15, 12, 0, 0)
        first = create_database_backup(engine, now=instant)
        second = create_database_backup(engine, now=instant)
        assert first != second
        assert values(first) == values(second) == [("kept",)]
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "database,query",
    [
        (":memory:", {}),
        (None, {}),
        ("file:shared", {"mode": "memory"}),
        ("file::memory:", {}),
    ],
)
def test_memory_database_is_skipped_without_files(
    tmp_path, monkeypatch, database, query
):
    from services.backup_service import create_database_backup

    monkeypatch.chdir(tmp_path)
    engine = SimpleNamespace(
        dialect=SimpleNamespace(name="sqlite"),
        url=SimpleNamespace(database=database, query=query),
    )
    assert create_database_backup(engine) is None
    assert list(tmp_path.iterdir()) == []


def test_non_sqlite_engine_is_skipped():
    from services.backup_service import create_database_backup

    engine = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    assert create_database_backup(engine) is None


def test_missing_database_is_not_created(tmp_path):
    from services.backup_service import create_database_backup

    source = tmp_path / "missing.db"
    engine = create_engine(f"sqlite:///{source}")
    try:
        with pytest.raises(FileNotFoundError):
            create_database_backup(engine)
        assert not source.exists()
        assert not (tmp_path / "backups").exists()
    finally:
        engine.dispose()


def test_failed_snapshot_does_not_rotate_existing_backups(tmp_path, monkeypatch):
    from services import backup_service

    source = tmp_path / "source.db"
    seed(source)
    app = backup_app(tmp_path, f"sqlite:///{source}")
    namespace = scheduler_functions(app)
    cleanup = Mock()
    namespace["cleanup_old_backups"] = cleanup

    def fail(*_args):
        raise OSError("simulated destination failure")

    monkeypatch.setattr(backup_service, "backup_sqlite_database", fail)
    try:
        namespace["backup_database"]()
        cleanup.assert_not_called()
        assert values(source) == [("kept",)]
        assert list((tmp_path / "backups").iterdir()) == []
    finally:
        with app.app_context():
            db.engine.dispose()


def test_cleanup_failure_does_not_escape_scheduler(tmp_path, monkeypatch):
    from services import backup_service

    def fail(*_args, **_kwargs):
        raise PermissionError("simulated retention permission error")

    monkeypatch.setattr(backup_service, "prune_database_backups", fail)
    namespace = scheduler_functions(SimpleNamespace(logger=Mock()))
    namespace["cleanup_old_backups"](tmp_path)
    namespace["app"].logger.warning.assert_called_once()


def test_rotation_keeps_exact_seven_day_boundary(tmp_path):
    from services.backup_service import prune_database_backups

    instant = datetime(2026, 11, 15, 12, 0, 0)
    expired = (
        tmp_path
        / "brick_manager_20260101_010101_000001_0123456789abcdef0123456789abcdef.backup.db"
    )
    boundary = tmp_path / "brick_manager_20260101_010102.backup.db"
    fresh = tmp_path / "brick_manager_20260101_010103.backup.db"
    for path, days in [(expired, 8), (boundary, 7), (fresh, 6)]:
        path.write_text("snapshot")
        timestamp = (instant - timedelta(days=days)).timestamp()
        os.utime(path, (timestamp, timestamp))
    assert prune_database_backups(tmp_path, now=instant) == [expired]
    assert boundary.exists() and fresh.exists()
