"""Native set-label PDFs, request validation, and transactional file failures."""

from io import BytesIO
from pathlib import Path

import pytest
from models import RebrickableSets, RebrickableThemes, User_Set, db
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4, landscape


@pytest.fixture
def label_copy(app, tmp_path, monkeypatch):
    db.session.add(RebrickableThemes(id=1, name="Dreamzzz"))
    db.session.flush()
    db.session.add(
        RebrickableSets(
            set_num="71486-1",
            name="Castle Nocturnia",
            year=2024,
            theme_id=1,
            num_parts=1805,
            img_url="https://example.test/castle.png",
        )
    )
    db.session.flush()
    db.session.add(User_Set(id=187, set_num="71486-1", label_printed=False))
    db.session.commit()
    # Flask(__name__) resolves a relative template_folder against root_path.
    # The shared test factory normally uses an absolute template folder.
    monkeypatch.setattr(app, "root_path", str(Path(__file__).parents[1]))
    monkeypatch.setattr(app, "template_folder", "templates")
    monkeypatch.setitem(app.config, "OUTPUT_FOLDER", str(tmp_path / "output"))
    monkeypatch.chdir(tmp_path)
    return 187


@pytest.mark.parametrize("size,pages", [("MB-1", 1), ("MB-4", 2), ("BIG-BOX", 3)])
def test_set_label_download_is_print_ready_pdf(app, client, label_copy, size, pages):
    response = client.post(
        "/set_maintain/generate_label",
        json={"set_id": str(label_copy), "box_size": size},
    )

    assert response.status_code == 200, response.get_json()
    assert response.mimetype == "application/pdf"
    assert f"187_{size}.pdf" in response.headers["Content-Disposition"]
    content = response.get_data()
    reader = PdfReader(BytesIO(content))
    assert len(reader.pages) == pages
    for page in reader.pages:
        assert (
            float(page.mediabox.width),
            float(page.mediabox.height),
        ) == pytest.approx(landscape(A4))
        assert "100%" in page.extract_text()
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "Castle Nocturnia" in text
    assert "71486-1" in text
    assert "187" in text
    assert reader.trailer["/Root"]["/ViewerPreferences"]["/PrintScaling"] == "/None"
    assert (
        Path(app.config["OUTPUT_FOLDER"]) / f"187_{size}.pdf"
    ).read_bytes() == content
    assert db.session.get(User_Set, label_copy).label_printed is True


def test_set_label_needs_no_external_template_folder(
    app, client, label_copy, monkeypatch
):
    monkeypatch.setattr(app, "template_folder", None)
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": "MB-4"}
    )
    assert response.status_code == 200
    assert len(PdfReader(BytesIO(response.data)).pages) == 2


@pytest.mark.parametrize("size", ["MB-1", "MB-4", "BIG-BOX"])
def test_set_label_preserves_catalog_characters(app, client, label_copy, size):
    name = 'Schloss "A & B" <keep> Größe BOX_ID'
    image_url = 'https://example.test/p.png?a=1&b="two"'
    catalog = db.session.get(RebrickableSets, "71486-1")
    catalog.name = name
    catalog.img_url = image_url
    db.session.commit()
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": size}
    )
    assert response.status_code == 200
    text = PdfReader(BytesIO(response.data)).pages[0].extract_text()
    assert name in " ".join(text.split())
    assert image_url.encode() not in response.data


def test_set_label_allows_missing_catalog_image(client, label_copy):
    db.session.get(RebrickableSets, "71486-1").img_url = None
    db.session.commit()
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": "MB-1"}
    )
    assert response.status_code == 200
    text = PdfReader(BytesIO(response.data)).pages[0].extract_text()
    assert "Image unavailable" in text
    assert response.headers["X-Label-Warning"]
    assert "None" not in text


@pytest.mark.parametrize(
    "payload",
    [
        [],
        "187",
        None,
        {},
        {"set_id": True, "box_size": "MB-4"},
        {"set_id": 187.5, "box_size": "MB-4"},
        {"set_id": -1, "box_size": "MB-4"},
        {"set_id": 0, "box_size": "MB-4"},
        {"set_id": "x", "box_size": "MB-4"},
        {"set_id": 187, "box_size": "../MB-4"},
        {"set_id": 187, "box_size": []},
        {"set_id": 187},
    ],
)
def test_set_label_rejects_invalid_request_without_changes(
    app, client, label_copy, payload
):
    response = client.post("/set_maintain/generate_label", json=payload)
    assert response.status_code == 400
    assert response.get_json()["error"]
    assert db.session.get(User_Set, label_copy).label_printed is False
    assert not Path(app.config["OUTPUT_FOLDER"]).exists()


def test_set_label_unknown_copy_does_not_create_output(app, client, label_copy):
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": 999, "box_size": "MB-4"}
    )
    assert response.status_code == 404
    assert db.session.get(User_Set, label_copy).label_printed is False
    assert not Path(app.config["OUTPUT_FOLDER"]).exists()


def test_set_label_missing_template_does_not_affect_pdf(
    app, client, label_copy, tmp_path, monkeypatch
):
    monkeypatch.setattr(app, "template_folder", str(tmp_path / "missing-templates"))
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": "MB-4"}
    )
    assert response.status_code == 200
    assert len(PdfReader(BytesIO(response.data)).pages) == 2
    assert db.session.get(User_Set, label_copy).label_printed is True


def test_set_label_failed_write_preserves_file_and_status(
    app, client, label_copy, monkeypatch
):
    folder = Path(app.config["OUTPUT_FOLDER"])
    folder.mkdir()
    previous = folder / "187_MB-4.pdf"
    previous.write_bytes(b"previous label")

    def fail_replace(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(Path, "replace", fail_replace)
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": "MB-4"}
    )
    assert response.status_code == 500
    assert db.session.get(User_Set, label_copy).label_printed is False
    assert previous.read_bytes() == b"previous label"
    assert list(folder.iterdir()) == [previous]


def test_set_label_failed_commit_rolls_back_printed_status(
    client, label_copy, monkeypatch
):
    def fail_commit():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db.session, "commit", fail_commit)
    response = client.post(
        "/set_maintain/generate_label", json={"set_id": label_copy, "box_size": "MB-1"}
    )
    assert response.status_code == 500
    assert db.session.get(User_Set, label_copy).label_printed is False
