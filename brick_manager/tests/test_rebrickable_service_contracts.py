"""Request, retry, and parameter contracts for the catalog API client."""

from unittest.mock import Mock, call

import pytest
import requests
from services.rebrickable_service import RebrickableAPIException, RebrickableService


def remote(status, payload=None, headers=None):
    response = Mock(status_code=status, headers=headers or {})
    response.json.return_value = payload or {}
    return response


def test_request_uses_authentication_timeout_and_returns_json(monkeypatch):
    get = Mock(return_value=remote(200, {"results": [1]}))
    monkeypatch.setattr(
        "services.rebrickable_service.Config.REBRICKABLE_TOKEN", "api-key"
    )
    monkeypatch.setattr("services.rebrickable_service.requests.get", get)

    result = RebrickableService._make_request("parts/", {"page": 2})

    assert result == {"results": [1]}
    get.assert_called_once_with(
        "https://rebrickable.com/api/v3/lego/parts/",
        headers={"Accept": "application/json", "Authorization": "key api-key"},
        params={"page": 2},
        timeout=30,
    )


def test_invalid_page_is_a_clean_pagination_end(monkeypatch):
    monkeypatch.setattr(
        "services.rebrickable_service.requests.get",
        Mock(return_value=remote(404, {"detail": "Invalid page."})),
    )

    assert RebrickableService._make_request("parts/", retries=1) is None


def test_rate_limit_honors_retry_after_then_retries(monkeypatch):
    get = Mock(
        side_effect=[
            remote(429, headers={"Retry-After": "2"}),
            remote(200, {"ok": True}),
        ]
    )
    sleep = Mock()
    monkeypatch.setattr("services.rebrickable_service.requests.get", get)
    monkeypatch.setattr("services.rebrickable_service.time.sleep", sleep)

    assert RebrickableService._make_request("colors/", retries=2) == {"ok": True}
    sleep.assert_called_once_with(2)


def test_timeout_retries_with_exponential_delay(monkeypatch):
    get = Mock(side_effect=[requests.ReadTimeout(), remote(200, {"recovered": True})])
    sleep = Mock()
    monkeypatch.setattr("services.rebrickable_service.requests.get", get)
    monkeypatch.setattr("services.rebrickable_service.time.sleep", sleep)
    monkeypatch.setattr(RebrickableService, "INITIAL_RETRY_DELAY", 3)

    assert RebrickableService._make_request("themes/", retries=2) == {"recovered": True}
    sleep.assert_called_once_with(3)


def test_permanent_network_error_is_wrapped(monkeypatch):
    monkeypatch.setattr(
        "services.rebrickable_service.requests.get",
        Mock(side_effect=requests.ConnectionError("secret endpoint failure")),
    )

    with pytest.raises(RebrickableAPIException, match="Request failed"):
        RebrickableService._make_request("parts/", retries=2)


def test_unsuccessful_responses_exhaust_bounded_retries(monkeypatch):
    get = Mock(return_value=remote(503))
    monkeypatch.setattr("services.rebrickable_service.requests.get", get)

    with pytest.raises(RebrickableAPIException, match="after 2 retries"):
        RebrickableService._make_request("parts/", retries=2)

    assert get.call_count == 2


def test_parts_wrapper_does_not_mutate_callers_filters(monkeypatch):
    request = Mock(return_value={"results": []})
    monkeypatch.setattr(RebrickableService, "_make_request", request)
    filters = {"part_cat_id": 4}

    result = RebrickableService.get_parts(
        filters, page=2, page_size=25, inc_part_details=True
    )

    assert result == {"results": []}
    assert filters == {"part_cat_id": 4}
    request.assert_called_once_with(
        "parts/",
        params={
            "part_cat_id": 4,
            "page": 2,
            "page_size": 25,
            "inc_part_details": 1,
        },
    )


def test_color_and_theme_wrappers_forward_pagination(monkeypatch):
    request = Mock(side_effect=[{"colors": []}, {"themes": []}])
    monkeypatch.setattr(RebrickableService, "_make_request", request)

    assert RebrickableService.get_colors(page=2, page_size=5) == {"colors": []}
    assert RebrickableService.get_themes(page=3, page_size=6) == {"themes": []}
    assert request.call_args_list == [
        call("colors/", params={"page": 2, "page_size": 5}),
        call("themes/", params={"page": 3, "page_size": 6}),
    ]
