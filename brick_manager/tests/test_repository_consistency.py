"""Repository contracts that prevent schema and status documentation drift."""

import json
import re
from pathlib import Path

from models import USER_SET_STATUSES, db

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_database_schema_documents_every_sqlalchemy_table():
    schema_document = (PROJECT_ROOT / "database_schema.md").read_text(encoding="utf-8")

    missing_tables = sorted(
        table_name
        for table_name in db.metadata.tables
        if f"`{table_name}`" not in schema_document
    )

    assert missing_tables == []


def test_set_maintenance_exposes_every_supported_status():
    template = (PROJECT_ROOT / "brick_manager/templates/set_maintain.html").read_text(
        encoding="utf-8"
    )
    option_values = set(re.findall(r'<option value="([a-z]+)">', template))

    assert option_values >= USER_SET_STATUSES


def test_documented_statuses_match_supported_statuses():
    schema_document = (PROJECT_ROOT / "database_schema.md").read_text(encoding="utf-8")
    documented_statuses = {
        status for status in USER_SET_STATUSES if f"`{status}`" in schema_document
    }

    assert documented_statuses == USER_SET_STATUSES


def test_vscode_uses_the_workspace_poetry_environment_without_fake_projects():
    settings = json.loads(
        (PROJECT_ROOT / ".vscode/settings.json").read_text(encoding="utf-8")
    )

    assert settings["python.defaultInterpreterPath"] == ".venv/bin/python"
    assert settings["python-envs.workspaceSearchPaths"] == ["./.venv"]
    assert settings["python-envs.pythonProjects"] == []
    assert (PROJECT_ROOT / settings["python.defaultInterpreterPath"]).is_file()
