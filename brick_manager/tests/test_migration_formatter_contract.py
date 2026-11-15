"""Automated fixers must not rewrite already-applied migration artifacts."""

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from pre_commit.commands.run import filter_by_include_exclude
from services.migration_service import apply_sqlite_migrations

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("command", [["format"], ["check", "--fix"]])
def test_explicit_ruff_invocation_preserves_applied_migration(tmp_path, command):
    shutil.copyfile(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    migrations = tmp_path / "brick_manager" / "migrations"
    migrations.mkdir(parents=True)
    artifact = migrations / "001_frozen.py"
    original = b"import os\n\ndef upgrade(connection):\n    connection.execute('CREATE TABLE records (id INTEGER)')\n    connection.execute('INSERT INTO records VALUES (1)')\n"
    artifact.write_bytes(original)
    database = tmp_path / "collection.db"
    apply_sqlite_migrations(database, migrations)
    result = subprocess.run(
        [sys.executable, "-m", "ruff", *command, str(artifact)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert artifact.read_bytes() == original
    apply_sqlite_migrations(database, migrations)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT id FROM records").fetchall() == [(1,)]


@pytest.mark.parametrize(
    "hook_id", ["trailing-whitespace", "end-of-file-fixer", "ruff-check", "ruff-format"]
)
def test_mutating_hooks_skip_migrations_but_keep_application_files(hook_id):
    configuration = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    hook = next(
        hook
        for repo in configuration["repos"]
        for hook in repo["hooks"]
        if hook["id"] == hook_id
    )
    selected = list(
        filter_by_include_exclude(
            [
                "brick_manager/migrations/001_frozen.py",
                "brick_manager/services/example.py",
            ],
            hook.get("files", ""),
            hook.get("exclude", "^$"),
        )
    )
    assert selected == ["brick_manager/services/example.py"]
