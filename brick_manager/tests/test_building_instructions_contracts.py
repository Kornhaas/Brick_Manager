"""Behavioral contracts for local building-instruction discovery and serving."""

from pathlib import Path

import pytest
from models import RebrickableSets, RebrickableThemes, User_Set, db
from routes.building_instructions import get_instruction_files_for_sets


@pytest.fixture
def instructions_folder(app, tmp_path):
    app.config["INSTRUCTIONS_FOLDER"] = str(tmp_path)
    return tmp_path


@pytest.fixture
def owned_set():
    theme = RebrickableThemes(name="Space")
    db.session.add(theme)
    db.session.flush()
    template = RebrickableSets(
        set_num="10751-1",
        name="Mountain Police Chase",
        year=2018,
        theme_id=theme.id,
        num_parts=297,
    )
    db.session.add(template)
    db.session.flush()
    user_set = User_Set(set_num=template.set_num, status="complete")
    db.session.add(user_set)
    db.session.commit()
    return user_set


def test_instruction_discovery_filters_sets_and_supported_file_types(
    app, instructions_folder
):
    matching = instructions_folder / "10751-1 instructions"
    matching.mkdir()
    (matching / "01-cover.jpg").write_bytes(b"jpg")
    (matching / "02-manual.pdf").write_bytes(b"pdf")
    (matching / "notes.txt").write_text("not an instruction")
    unrelated = instructions_folder / "99999-1"
    unrelated.mkdir()
    (unrelated / "manual.pdf").write_bytes(b"pdf")

    with app.app_context():
        result = get_instruction_files_for_sets({"10751"})

    assert list(result) == ["10751"]
    assert [item["name"] for item in result["10751"]] == [
        "01-cover.jpg",
        "02-manual.pdf",
    ]
    assert [item["type"] for item in result["10751"]] == ["image", "pdf"]


def test_building_instructions_page_lists_owned_sets_with_local_files(
    client, instructions_folder, owned_set
):
    set_folder = instructions_folder / "10751-1"
    set_folder.mkdir()
    (set_folder / "manual.pdf").write_bytes(b"manual")

    response = client.get("/building_instructions")

    assert response.status_code == 200
    assert b"Mountain Police Chase" in response.data
    assert b"manual.pdf" in response.data


def test_instruction_download_serves_supported_file(client, instructions_folder):
    set_folder = instructions_folder / "10751-1"
    set_folder.mkdir()
    instruction = set_folder / "manual.pdf"
    instruction.write_bytes(b"%PDF-test")

    response = client.get("/building_instructions/download/10751-1/manual.pdf")

    assert response.status_code == 200
    assert response.data == b"%PDF-test"


@pytest.mark.parametrize(
    "path",
    [
        "10751-1/notes.txt",
        "10751-1/missing.pdf",
        "../../etc/passwd",
    ],
)
def test_instruction_download_rejects_unsafe_or_unsupported_paths(
    client, instructions_folder, path
):
    set_folder = instructions_folder / "10751-1"
    set_folder.mkdir(exist_ok=True)
    (set_folder / "notes.txt").write_text("secret")

    response = client.get(f"/building_instructions/download/{path}")

    assert response.status_code == 404


def test_instruction_discovery_creates_configured_folder_without_results(app, tmp_path):
    missing = Path(tmp_path) / "not-created"
    app.config["INSTRUCTIONS_FOLDER"] = str(missing)

    with app.app_context():
        assert get_instruction_files_for_sets({"10751"}) == {}
    assert missing.is_dir()
