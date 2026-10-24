"""Network and reconciliation contracts for owned-set synchronization."""

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
from services import rebrickable_sets_sync_service as service


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setattr(
        service, "get_rebrickable_user_token", Mock(return_value="user-token")
    )
    monkeypatch.setattr(
        service, "get_rebrickable_api_key", Mock(return_value="api-key")
    )


def response(status, payload=None):
    remote = Mock(status_code=status, text="remote-secret")
    remote.json.return_value = payload
    return remote


def expected_headers(json=False):
    headers = {"Accept": "application/json", "Authorization": "key api-key"}
    if json:
        headers["Content-Type"] = "application/json"
    return headers


def test_get_lists_requires_credentials(monkeypatch):
    monkeypatch.setattr(service, "get_rebrickable_user_token", Mock(return_value=None))
    monkeypatch.setattr(
        service, "get_rebrickable_api_key", Mock(return_value="api-key")
    )

    assert service.get_rebrickable_lists() == []


def test_get_lists_uses_bounded_authenticated_request(credentials, monkeypatch):
    get = Mock(return_value=response(200, {"results": [{"id": 7}]}))
    monkeypatch.setattr(service.requests, "get", get)

    assert service.get_rebrickable_lists() == [{"id": 7}]
    get.assert_called_once_with(
        "https://rebrickable.com/api/v3/users/user-token/setlists/",
        headers=expected_headers(),
        timeout=20,
    )


def test_create_list_uses_json_contract(credentials, monkeypatch):
    post = Mock(return_value=response(201, {"id": 12}))
    monkeypatch.setattr(service.requests, "post", post)

    result = service.create_brick_manager_list()

    assert result == {
        "success": True,
        "list_id": 12,
        "message": "Brick_Manager list created successfully",
    }
    post.assert_called_once_with(
        "https://rebrickable.com/api/v3/users/user-token/setlists/",
        json={"name": "Brick_Manager", "is_buildable": True},
        headers=expected_headers(json=True),
        timeout=20,
    )


def test_create_list_does_not_expose_remote_error_body(credentials, monkeypatch):
    monkeypatch.setattr(service.requests, "post", Mock(return_value=response(403)))

    result = service.create_brick_manager_list()

    assert result == {"success": False, "message": "Failed to create list: HTTP 403"}
    assert "remote-secret" not in result["message"]


def test_get_brick_manager_list_prefers_existing_list(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_rebrickable_lists",
        Mock(
            return_value=[
                {"id": 1, "name": "Other"},
                {"id": 2, "name": "Brick_Manager"},
            ]
        ),
    )
    create = Mock()
    monkeypatch.setattr(service, "create_brick_manager_list", create)

    result = service.get_brick_manager_list()

    assert result["list_id"] == 2
    assert result["created"] is False
    create.assert_not_called()


def test_get_brick_manager_list_marks_new_list(monkeypatch):
    monkeypatch.setattr(service, "get_rebrickable_lists", Mock(return_value=[]))
    monkeypatch.setattr(
        service,
        "create_brick_manager_list",
        Mock(return_value={"success": True, "list_id": 3}),
    )

    assert service.get_brick_manager_list() == {
        "success": True,
        "list_id": 3,
        "created": True,
    }


def test_get_list_sets_follows_pagination(credentials, monkeypatch):
    get = Mock(
        side_effect=[
            response(200, {"results": [{"set": {"set_num": "1-1"}}], "next": "page2"}),
            response(200, {"results": [{"set": {"set_num": "2-1"}}], "next": None}),
        ]
    )
    monkeypatch.setattr(service.requests, "get", get)

    result = service.get_list_sets(9)

    assert [item["set"]["set_num"] for item in result] == ["1-1", "2-1"]
    url = "https://rebrickable.com/api/v3/users/user-token/setlists/9/sets/"
    assert get.call_args_list == [
        call(
            url,
            headers=expected_headers(),
            params={"page": 1, "page_size": 100},
            timeout=20,
        ),
        call(
            url,
            headers=expected_headers(),
            params={"page": 2, "page_size": 100},
            timeout=20,
        ),
    ]


def test_add_sets_short_circuits_empty_input(credentials, monkeypatch):
    post = Mock()
    monkeypatch.setattr(service.requests, "post", post)

    result = service.add_sets_to_list(9, {})

    assert result["success"] is True
    assert result["added_count"] == 0
    post.assert_not_called()


def test_add_sets_bulk_request_preserves_quantities(credentials, monkeypatch):
    post = Mock(return_value=response(201, [{"id": 1}, {"id": 2}]))
    monkeypatch.setattr(service.requests, "post", post)

    result = service.add_sets_to_list(9, {"1-1": 2, "2-1": 1})

    assert result["added_count"] == 2
    post.assert_called_once_with(
        "https://rebrickable.com/api/v3/users/user-token/setlists/9/sets/",
        json=[{"set_num": "1-1", "quantity": 2}, {"set_num": "2-1", "quantity": 1}],
        headers=expected_headers(json=True),
        timeout=60,
    )


def test_bulk_rate_limit_falls_back_to_individual_requests(credentials, monkeypatch):
    monkeypatch.setattr(service.requests, "post", Mock(return_value=response(429)))
    fallback = Mock(return_value={"success": True, "added_count": 1})
    monkeypatch.setattr(service, "add_sets_individually", fallback)

    result = service.add_sets_to_list(4, ["1-1"])

    assert result["added_count"] == 1
    fallback.assert_called_once_with(
        4, [("1-1", 1)], expected_headers(json=True), "user-token"
    )


def test_individual_addition_reports_success_rate_limits_and_errors(monkeypatch):
    monkeypatch.setattr(
        service.requests,
        "post",
        Mock(side_effect=[response(201), response(429), response(400)]),
    )

    result = service.add_sets_individually(
        4, [("1-1", 1), ("2-1", 2), ("3-1", 3)], expected_headers(), "user-token"
    )

    assert result["added_count"] == 1
    assert result["rate_limited_count"] == 1
    assert result["errors"] == ["Failed to add 3-1 (qty: 3): HTTP 400"]
    assert "remote-secret" not in str(result)


@pytest.mark.parametrize(
    ("delete_status", "add_status", "success", "rate_limited"),
    [(204, 201, True, False), (404, 429, False, True), (500, 201, False, False)],
)
def test_quantity_update_contract(
    credentials, monkeypatch, delete_status, add_status, success, rate_limited
):
    monkeypatch.setattr(
        service.requests, "delete", Mock(return_value=response(delete_status))
    )
    post = Mock(return_value=response(add_status))
    monkeypatch.setattr(service.requests, "post", post)

    result = service.update_set_quantity_in_list(4, "1-1", 3)

    assert result["success"] is success
    assert result.get("rate_limited", False) is rate_limited
    if delete_status == 500:
        post.assert_not_called()


def test_remove_sets_reports_partial_result_without_remote_body(
    credentials, monkeypatch
):
    monkeypatch.setattr(
        service.requests, "delete", Mock(side_effect=[response(204), response(500)])
    )

    result = service.remove_sets_from_list(4, ["1-1", "2-1"])

    assert result["removed_count"] == 1
    assert result["errors"] == ["Failed to remove 2-1: HTTP 500"]
    assert "remote-secret" not in str(result)


def test_sync_reconciles_add_update_and_remove(monkeypatch):
    local = [
        SimpleNamespace(template_set=SimpleNamespace(set_num="new-1")),
        SimpleNamespace(template_set=SimpleNamespace(set_num="same-1")),
        SimpleNamespace(template_set=SimpleNamespace(set_num="same-1")),
    ]
    query = Mock()
    query.all.return_value = local
    monkeypatch.setattr(service.db.session, "query", Mock(return_value=query))
    monkeypatch.setattr(
        service,
        "get_brick_manager_list",
        Mock(return_value={"success": True, "list_id": 8, "created": False}),
    )
    monkeypatch.setattr(
        service,
        "get_list_sets",
        Mock(
            return_value=[
                {"set": {"set_num": "same-1"}, "quantity": 1},
                {"set": {"set_num": "old-1"}, "quantity": 1},
            ]
        ),
    )
    add = Mock(
        return_value={"success": True, "added_count": 1, "rate_limited_count": 0}
    )
    update = Mock(return_value={"success": True, "updated_count": 1})
    remove = Mock(return_value={"success": True, "removed_count": 1})
    monkeypatch.setattr(service, "add_sets_to_list", add)
    monkeypatch.setattr(service, "update_set_quantity_in_list", update)
    monkeypatch.setattr(service, "remove_sets_from_list", remove)

    result = service.sync_user_sets_with_rebrickable()

    assert result["success"] is True
    assert result["summary"]["sets_added"] == 1
    assert result["summary"]["sets_updated"] == 1
    assert result["summary"]["sets_removed"] == 1
    add.assert_called_once_with(8, {"new-1": 1})
    update.assert_called_once_with(8, "same-1", 2)
    assert remove.call_args.args[0] == 8
    assert set(remove.call_args.args[1]) == {"old-1"}
