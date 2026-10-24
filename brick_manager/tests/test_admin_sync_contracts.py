"""HTTP contracts for manually triggered Rebrickable synchronization."""

from unittest.mock import Mock

import pytest
from routes import admin_sync


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setattr(
        admin_sync, "get_rebrickable_user_token", Mock(return_value="token")
    )
    monkeypatch.setattr(admin_sync, "get_rebrickable_api_key", Mock(return_value="key"))


def test_admin_page_reflects_credential_availability(client, monkeypatch):
    monkeypatch.setattr(
        admin_sync, "get_rebrickable_user_token", Mock(return_value=None)
    )
    monkeypatch.setattr(admin_sync, "get_rebrickable_api_key", Mock(return_value="key"))

    response = client.get("/admin/sync")

    assert response.status_code == 200
    assert b"Please configure your Rebrickable User Token" in response.data
    assert b"Start Sync" in response.data


@pytest.mark.parametrize(
    ("token", "key", "message"),
    [
        (None, None, "Missing: User Token, API Key"),
        ("token", None, "Missing: API Key"),
        (None, "key", "Missing: User Token"),
        ("token", "key", "Sync available - tokens configured"),
    ],
)
def test_availability_reports_each_credential(client, monkeypatch, token, key, message):
    monkeypatch.setattr(
        admin_sync, "get_rebrickable_user_token", Mock(return_value=token)
    )
    monkeypatch.setattr(admin_sync, "get_rebrickable_api_key", Mock(return_value=key))

    response = client.get("/admin/sync/check_availability")

    assert response.status_code == 200
    assert response.get_json()["available"] is bool(token and key)
    assert response.get_json()["message"] == message


@pytest.mark.parametrize(
    "path",
    [
        "/admin/sync/missing_parts",
        "/admin/sync/missing_minifigure_parts",
        "/admin/sync/all_missing_parts",
        "/admin/sync/user_sets",
    ],
)
def test_sync_endpoints_fail_closed_without_credentials(client, monkeypatch, path):
    monkeypatch.setattr(
        admin_sync, "get_rebrickable_user_token", Mock(return_value=None)
    )
    monkeypatch.setattr(admin_sync, "get_rebrickable_api_key", Mock(return_value=None))

    response = client.post(path, json={})

    assert response.status_code == 400
    assert response.get_json()["success"] is False


@pytest.mark.parametrize(
    "payload", [[], {"batch_size": True}, {"batch_size": 0}, {"batch_size": "10"}]
)
def test_missing_parts_rejects_invalid_batch_size(client, credentials, payload):
    response = client.post("/admin/sync/missing_parts", json=payload)

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_missing_parts_passes_batch_and_surfaces_rate_limit_summary(
    client, credentials, monkeypatch
):
    sync = Mock(
        return_value={
            "success": True,
            "summary": {"missing_parts_add_result": {"rate_limited_count": 2}},
        }
    )
    monkeypatch.setattr(admin_sync, "sync_missing_parts_with_rebrickable", sync)

    response = client.post("/admin/sync/missing_parts", json={"batch_size": 25})

    assert response.status_code == 200
    assert response.get_json()["summary"]["rate_limited_count"] == 2
    sync.assert_called_once_with(batch_size=25)


def test_minifigure_sync_maps_service_failure_to_500(client, credentials, monkeypatch):
    sync = Mock(return_value={"success": False, "message": "remote rejected request"})
    monkeypatch.setattr(
        admin_sync, "sync_missing_minifigure_parts_with_rebrickable", sync
    )

    response = client.post("/admin/sync/missing_minifigure_parts", json={})

    assert response.status_code == 500
    assert response.get_json()["message"] == "remote rejected request"
    sync.assert_called_once_with(batch_size=None)


def test_combined_sync_aggregates_both_summaries(client, credentials, monkeypatch):
    monkeypatch.setattr(
        admin_sync,
        "sync_missing_parts_with_rebrickable",
        Mock(
            return_value={
                "success": True,
                "summary": {
                    "local_missing_count": 4,
                    "actual_added": 2,
                    "actual_removed": 1,
                    "list_id": 10,
                },
            }
        ),
    )
    monkeypatch.setattr(
        admin_sync,
        "sync_missing_minifigure_parts_with_rebrickable",
        Mock(
            return_value={
                "success": True,
                "summary": {
                    "local_missing_count": 3,
                    "actual_added": 1,
                    "actual_removed": 0,
                    "list_id": 20,
                },
            }
        ),
    )

    response = client.post("/admin/sync/all_missing_parts", json={"batch_size": 5})

    assert response.status_code == 200
    summary = response.get_json()["summary"]
    assert summary["regular_local_count"] == 4
    assert summary["minifig_local_count"] == 3
    assert summary["regular_list_id"] == 10
    assert summary["minifig_list_id"] == 20
    assert "Added 3, removed 1" in summary["message"]


def test_sync_exception_is_hidden_from_client(client, credentials, monkeypatch):
    monkeypatch.setattr(
        admin_sync,
        "sync_missing_parts_with_rebrickable",
        Mock(side_effect=RuntimeError("internal secret")),
    )

    response = client.post("/admin/sync/missing_parts", json={})

    assert response.status_code == 500
    assert response.get_json() == {
        "success": False,
        "message": "Missing parts synchronization failed.",
    }
    assert b"internal secret" not in response.data
