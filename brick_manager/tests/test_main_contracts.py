"""Behavioral contracts for health, cache serving, and debug boundaries."""

from unittest.mock import patch


def test_health_reports_database_connectivity(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "message": "Application is running properly",
        "database": "connected",
    }


def test_health_rolls_back_and_hides_database_error(client):
    with (
        patch("routes.main.db.session.execute", side_effect=RuntimeError("db secret")),
        patch("routes.main.db.session.rollback") as rollback,
    ):
        response = client.get("/health")

    assert response.status_code == 500
    assert response.get_json() == {
        "status": "unhealthy",
        "message": "Health check failed",
        "database": "disconnected",
    }
    assert b"db secret" not in response.data
    rollback.assert_called_once()


def test_cached_image_is_served_from_configured_directory(app, client, tmp_path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "part.png").write_bytes(b"png-data")
    app.config["CACHE_FOLDER"] = str(tmp_path)

    response = client.get("/cache/images/part.png")

    assert response.status_code == 200
    assert response.data == b"png-data"


def test_cached_image_rejects_unsafe_filename(client):
    response = client.get("/cache/images/..secret.png")

    assert response.status_code == 404


def test_cache_debug_endpoint_is_hidden_outside_debug_and_testing(
    app, client, monkeypatch
):
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setitem(app.config, "DEBUG", False)

    response = client.get("/debug/cache")

    assert response.status_code == 404


def test_cache_debug_endpoint_uses_mocked_external_boundary(app, client, tmp_path):
    app.config["CACHE_FOLDER"] = str(tmp_path)
    (tmp_path / "existing.png").write_bytes(b"image")

    with (
        patch("services.cache_service.get_cache_directory", return_value=str(tmp_path)),
        patch("services.cache_service.cache_image", return_value="/cached/test.png"),
    ):
        response = client.get("/debug/cache")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["test_result"] == "Success: /cached/test.png"
    assert payload["cached_files_before"] == ["existing.png"]
