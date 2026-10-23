"""Behavioral contracts for encrypted Rebrickable credentials and routes."""

import base64
from unittest.mock import Mock

import pytest
import requests
from cryptography.fernet import Fernet
from models import ConfigSettings, db
from services import token_service


def add_setting(key, value, *, encrypted=False):
    setting = ConfigSettings(key=key, value=value, encrypted=encrypted)
    db.session.add(setting)
    db.session.commit()
    return setting


def test_service_decrypts_a_stored_user_token():
    key = Fernet.generate_key()
    encrypted = Fernet(key).encrypt(b"user-token").decode()
    add_setting("encryption_key", base64.b64encode(key).decode())
    add_setting("rebrickable_user_token", encrypted, encrypted=True)

    assert token_service.get_rebrickable_user_token() == "user-token"


def test_service_returns_none_for_missing_or_invalid_encryption_material():
    assert token_service.get_encryption_key() is None
    assert token_service.decrypt_token("not-a-token") is None

    add_setting("encryption_key", "not-base64")
    assert token_service.get_encryption_key() is None
    assert token_service.decrypt_token("not-a-token") is None


def test_service_builds_headers_without_exposing_an_absent_user_token():
    add_setting("rebrickable_api_key", "api-key")

    assert token_service.get_rebrickable_headers() == {
        "Accept": "application/json",
        "Authorization": "key api-key",
    }
    assert token_service.is_user_token_configured() is False


def test_service_builds_headers_with_decrypted_user_token():
    key = Fernet.generate_key()
    add_setting("encryption_key", base64.b64encode(key).decode())
    add_setting("rebrickable_api_key", "api-key")
    add_setting(
        "rebrickable_user_token",
        Fernet(key).encrypt(b"user-token").decode(),
        encrypted=True,
    )

    headers = token_service.get_rebrickable_headers()

    assert headers == {
        "Accept": "application/json",
        "Authorization": "key api-key",
        "User-Token": "user-token",
    }
    assert token_service.is_user_token_configured() is True


def test_service_refuses_headers_without_api_key():
    assert token_service.get_rebrickable_api_key() is None
    assert token_service.get_rebrickable_headers() is None


def test_token_page_shows_configuration_without_rendering_secret(client):
    add_setting("rebrickable_user_token", "encrypted-secret", encrypted=True)
    add_setting("rebrickable_username", "alice")

    response = client.get("/token_management")

    assert response.status_code == 200
    assert b"Token is configured" in response.data
    assert b"alice" in response.data
    assert b"encrypted-secret" not in response.data


def test_generate_token_requires_credentials_and_api_key(client):
    missing_credentials = client.post("/generate_token", data={})
    missing_key = client.post(
        "/generate_token", data={"username": "alice", "password": "secret"}
    )

    assert missing_credentials.get_json()["success"] is False
    assert missing_key.get_json() == {
        "success": False,
        "message": "Rebrickable API key not configured. Please contact administrator.",
    }


def test_generate_token_calls_remote_boundary_and_encrypts_result(client, monkeypatch):
    add_setting("rebrickable_api_key", "api-key")
    response = Mock(status_code=201)
    response.json.return_value = {"user_token": "remote-user-token"}
    post = Mock(return_value=response)
    monkeypatch.setattr("routes.token_management.requests.post", post)

    result = client.post(
        "/generate_token", data={"username": "alice", "password": "password"}
    )

    assert result.get_json()["success"] is True
    post.assert_called_once_with(
        "https://rebrickable.com/api/v3/users/_token/",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": "key api-key",
        },
        data={"username": "alice", "password": "password"},
        timeout=30,
    )
    stored = ConfigSettings.query.filter_by(key="rebrickable_user_token").one()
    assert stored.encrypted is True
    assert stored.value != "remote-user-token"
    assert (
        ConfigSettings.query.filter_by(key="rebrickable_username").one().value
        == "alice"
    )


@pytest.mark.parametrize(
    ("remote", "message"),
    [
        (requests.exceptions.Timeout(), "Timeout connecting to Rebrickable API"),
        (
            requests.exceptions.ConnectionError("offline"),
            "Network error connecting to Rebrickable API",
        ),
    ],
)
def test_generate_token_handles_network_failures(client, monkeypatch, remote, message):
    add_setting("rebrickable_api_key", "api-key")
    monkeypatch.setattr(
        "routes.token_management.requests.post", Mock(side_effect=remote)
    )

    response = client.post(
        "/generate_token", data={"username": "alice", "password": "password"}
    )

    assert response.get_json() == {"success": False, "message": message}
    assert ConfigSettings.query.filter_by(key="rebrickable_user_token").first() is None


def test_generate_token_rejects_malformed_success_response(client, monkeypatch):
    add_setting("rebrickable_api_key", "api-key")
    remote = Mock(status_code=200)
    remote.json.return_value = {"unexpected": True}
    monkeypatch.setattr(
        "routes.token_management.requests.post", Mock(return_value=remote)
    )

    response = client.post(
        "/generate_token", data={"username": "alice", "password": "password"}
    )

    assert response.get_json()["message"] == "Invalid response from Rebrickable API"


def test_delete_token_is_idempotently_reported(client):
    absent = client.post("/delete_token")
    token = add_setting("rebrickable_user_token", "encrypted", encrypted=True)
    present = client.post("/delete_token")

    assert absent.get_json()["success"] is False
    assert present.get_json()["success"] is True
    assert db.session.get(ConfigSettings, token.id) is None


def test_token_test_calls_profile_endpoint_with_decrypted_token(client, monkeypatch):
    key = Fernet.generate_key()
    add_setting("encryption_key", base64.b64encode(key).decode())
    add_setting("rebrickable_api_key", "api-key")
    add_setting(
        "rebrickable_user_token",
        Fernet(key).encrypt(b"user-token").decode(),
        encrypted=True,
    )
    remote = Mock(status_code=200)
    remote.json.return_value = {"username": "alice"}
    get = Mock(return_value=remote)
    monkeypatch.setattr("routes.token_management.requests.get", get)

    response = client.post("/test_token")

    assert response.get_json() == {
        "success": True,
        "message": "Token is valid! Connected as user: alice",
    }
    get.assert_called_once_with(
        "https://rebrickable.com/api/v3/users/user-token/profile/",
        headers={"Accept": "application/json", "Authorization": "key api-key"},
        timeout=30,
    )


def test_token_test_requires_stored_token_and_api_key(client):
    no_token = client.post("/test_token")
    key = Fernet.generate_key()
    add_setting("encryption_key", base64.b64encode(key).decode())
    add_setting(
        "rebrickable_user_token",
        Fernet(key).encrypt(b"token").decode(),
        encrypted=True,
    )
    no_api_key = client.post("/test_token")

    assert no_token.get_json()["message"] == "No token found to test"
    assert no_api_key.get_json()["message"] == "Rebrickable API key not configured"
