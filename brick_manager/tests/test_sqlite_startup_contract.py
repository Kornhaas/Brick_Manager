"""Exercise the real Flask loader with a disposable, initially missing directory."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def test_flask_cli_loads_and_migrates_nested_sqlite_path(tmp_path):
    root = Path(__file__).resolve().parents[2]
    selected = tmp_path / "selected collection" / "data" / "instance" / "collection.db"
    environment = os.environ.copy()
    environment.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{selected}",
        FLASK_SKIP_DOTENV="1",
        REBRICKABLE_TOKEN="",
        PYTHONPATH=str(root / "brick_manager") + os.pathsep + str(root),
        STARTUP_TEST_LOGS=str(tmp_path / "logs"),
    )
    code = """
import os
from unittest.mock import patch
from config import Config
Config.LOG_FOLDER = os.environ['STARTUP_TEST_LOGS']
from flask.cli import cli
with patch('apscheduler.schedulers.background.BackgroundScheduler'):
    cli.main(args=['--app', 'brick_manager/app.py', 'routes'], standalone_mode=False)
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "/warehouse" in result.stdout
    with sqlite3.connect(selected) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            == 2
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            connection.execute("SELECT COUNT(*) FROM part_storage").fetchone()[0] == 0
        )
