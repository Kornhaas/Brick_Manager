"""Transactional and network-boundary contracts for catalog CSV imports."""

import gzip
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call

import pytest
import requests
from models import RebrickablePartCategories, db
from routes import import_rebrickable_data as importer


class StreamingResponse:
    """Small context-managed response double for streamed downloads."""

    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        if self.error:
            raise self.error

    def iter_content(self, chunk_size):
        assert chunk_size == 8192
        return [self.payload[:4], b"", self.payload[4:]]


def compressed(content):
    output = BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb") as archive:
        archive.write(content)
    return output.getvalue()


def test_download_extracts_stream_atomically(tmp_path, monkeypatch):
    get = Mock(return_value=StreamingResponse(compressed(b"id,name\n1,Brick\n")))
    monkeypatch.setattr(importer, "IMPORT_DIR", str(tmp_path))
    monkeypatch.setattr(importer.requests, "get", get)

    result = importer.download_and_extract_csv("part_categories.csv.gz")

    assert Path(result).read_bytes() == b"id,name\n1,Brick\n"
    assert not list(tmp_path.glob("*.part"))
    assert not list(tmp_path.glob("*.gz"))
    get.assert_called_once_with(
        f"{importer.BASE_URL}/part_categories.csv.gz", stream=True, timeout=30
    )


def test_download_failure_removes_partial_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(importer, "IMPORT_DIR", str(tmp_path))
    monkeypatch.setattr(
        importer.requests,
        "get",
        Mock(return_value=StreamingResponse(b"", requests.HTTPError("503"))),
    )

    with pytest.raises(requests.HTTPError):
        importer.download_and_extract_csv("colors.csv.gz")

    assert list(tmp_path.iterdir()) == []


def test_import_replaces_catalog_rows_and_removes_csv(tmp_path):
    db.session.add(RebrickablePartCategories(id=1, name="Old"))
    db.session.commit()
    csv_path = tmp_path / "part_categories.csv"
    csv_path.write_text("id,name\n2,New\n", encoding="utf-8")

    importer.import_csv_to_sqlite(str(csv_path), RebrickablePartCategories)

    assert [(row.id, row.name) for row in RebrickablePartCategories.query.all()] == [
        (2, "New")
    ]
    assert not csv_path.exists()


def test_import_rolls_back_delete_and_keeps_csv_when_append_fails(
    tmp_path, monkeypatch
):
    db.session.add(RebrickablePartCategories(id=1, name="Preserved"))
    db.session.commit()
    csv_path = tmp_path / "part_categories.csv"
    csv_path.write_text("id,name\n2,New\n", encoding="utf-8")
    frame = Mock()
    frame.to_sql.side_effect = RuntimeError("write failed")
    monkeypatch.setattr(importer.pd, "read_csv", Mock(return_value=frame))

    with pytest.raises(RuntimeError, match="write failed"):
        importer.import_csv_to_sqlite(str(csv_path), RebrickablePartCategories)

    db.session.expire_all()
    assert RebrickablePartCategories.query.one().name == "Preserved"
    assert csv_path.exists()


def test_import_route_orchestrates_all_catalog_files(client, monkeypatch):
    ensure = Mock()
    download = Mock(side_effect=lambda name: f"/tmp/{name[:-3]}")
    load = Mock()
    models = {name: Mock(__tablename__=name) for name in importer.FILES}
    monkeypatch.setattr(importer, "ensure_table_structure", ensure)
    monkeypatch.setattr(importer, "download_and_extract_csv", download)
    monkeypatch.setattr(importer, "import_csv_to_sqlite", load)
    monkeypatch.setattr(importer, "_get_model_map", Mock(return_value=models))

    response = client.post("/import_data")

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
    ensure.assert_called_once_with()
    assert download.call_args_list == [call(name) for name in importer.FILES]
    assert load.call_args_list == [
        call(f"/tmp/{name[:-3]}", models[name]) for name in importer.FILES
    ]


def test_import_route_rolls_back_and_hides_internal_failure(client, monkeypatch):
    monkeypatch.setattr(
        importer, "ensure_table_structure", Mock(side_effect=RuntimeError("secret"))
    )
    rollback = Mock(wraps=db.session.rollback)
    monkeypatch.setattr(db.session, "rollback", rollback)

    response = client.post("/import_data")

    assert response.status_code == 500
    assert response.get_json() == {
        "status": "error",
        "message": "An unexpected error occurred. Changes rolled back.",
    }
    assert b"secret" not in response.data
    rollback.assert_called_once_with()


def test_import_page_renders(client):
    response = client.get("/import_data")

    assert response.status_code == 200
    assert b"Import" in response.data
