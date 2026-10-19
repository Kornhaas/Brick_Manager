"""Behavioural contracts for the Rebrickable missing-parts integration."""

from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import pytest
from services import rebrickable_sync_service as sync


def response(status_code, payload=None, text="error"):
    """Create the small HTTP response surface used by the service."""
    result = Mock(status_code=status_code, text=text)
    result.json.return_value = payload if payload is not None else []
    return result


@pytest.fixture(autouse=True)
def reset_rate_limit_tracker():
    """Keep global rate-limit state from leaking between contracts."""
    sync._rate_limit_tracker.update(
        consecutive_hits=0, last_hit_time=0, should_throttle=False
    )


def test_rate_limit_tracker_throttles_then_expires():
    """Three consecutive 429s pause calls, then the cooldown restores them."""
    with patch("services.rebrickable_sync_service.time.time", return_value=100):
        for _ in range(3):
            sync.update_rate_limit_tracker(True)

    with patch("services.rebrickable_sync_service.time.time", return_value=100):
        assert sync.should_skip_api_calls() is True

    with patch("services.rebrickable_sync_service.time.time", return_value=131):
        assert sync.should_skip_api_calls() is False
    assert sync._rate_limit_tracker["consecutive_hits"] == 0


def test_rate_limited_request_retries_get_and_preserves_request_contract():
    """A transient 429 uses backoff and retries the exact GET request."""
    rate_limited = response(429)
    succeeded = response(200, {"results": []})

    with (
        patch(
            "services.rebrickable_sync_service.requests.get",
            side_effect=[rate_limited, succeeded],
        ) as get,
        patch("services.rebrickable_sync_service.time.sleep") as sleep,
    ):
        result = sync.make_rate_limited_request(
            "https://example.invalid/items",
            {"Authorization": "key test"},
            {"page": 2},
            timeout=12,
        )

    assert result is succeeded
    assert get.call_count == 2
    get.assert_called_with(
        "https://example.invalid/items",
        headers={"Authorization": "key test"},
        params={"page": 2},
        timeout=12,
    )
    sleep.assert_called_once_with(1)


def test_rate_limited_request_returns_none_for_unknown_method():
    assert sync.make_rate_limited_request("url", {}, method="PATCH") is None


def test_find_inventory_part_prefers_owned_set_and_returns_exact_color_match():
    """The lookup uses the owned set and rejects same-part wrong-color results."""
    backup = response(200, {"results": [{"set_num": "backup-1"}]})
    inventory = response(
        200,
        {
            "results": [
                {"id": 1, "part": {"part_num": "3001"}, "color": {"id": 1}},
                {"id": 44, "part": {"part_num": "3001"}, "color": {"id": 5}},
            ]
        },
    )
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="api",
        ),
        patch(
            "services.rebrickable_sync_service.make_rate_limited_request",
            side_effect=[backup, inventory],
        ) as request,
    ):
        assert sync.find_inventory_part_id_from_user_sets("3001", 5, "owned-1") == 44

    assert request.call_args_list[1] == call(
        "https://rebrickable.com/api/v3/lego/sets/owned-1/parts/",
        {"Accept": "application/json", "Authorization": "key api"},
        {"part_num": "3001", "page_size": 100},
        timeout=20,
    )


def test_find_inventory_part_does_not_call_remote_without_api_key():
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value=None,
        ),
        patch("services.rebrickable_sync_service.make_rate_limited_request") as request,
    ):
        assert sync.find_inventory_part_id_from_user_sets("3001", 5) is None
    request.assert_not_called()


def test_local_missing_parts_filters_spares_and_includes_minifigures():
    regular = SimpleNamespace(
        parts_in_set=[
            SimpleNamespace(
                part_num="3001", color_id=1, quantity=4, have_quantity=1, is_spare=False
            ),
            SimpleNamespace(
                part_num="3002", color_id=2, quantity=2, have_quantity=0, is_spare=True
            ),
        ],
        set_num="set-1",
    )
    mini = SimpleNamespace(
        part_num="m1", color_id=3, quantity=3, have_quantity=1, is_spare=False
    )
    with (
        patch(
            "services.rebrickable_sync_service.User_Set",
            query=Mock(all=Mock(return_value=[regular])),
        ),
        patch(
            "services.rebrickable_sync_service.UserMinifigurePart",
            query=Mock(all=Mock(return_value=[mini])),
        ),
    ):
        assert sync.get_local_missing_parts() == [
            {
                "part_num": "3001",
                "color_id": 1,
                "missing_quantity": 3,
                "set_num": "set-1",
                "is_spare": False,
            },
            {
                "part_num": "m1",
                "color_id": 3,
                "missing_quantity": 2,
                "set_num": None,
                "is_spare": False,
                "is_minifig": True,
            },
        ]


def test_get_rebrickable_lost_parts_follows_pagination_and_authenticates():
    pages = [
        response(200, {"results": [{"id": 1}], "next": "next-page"}),
        response(200, {"results": [{"id": 2}], "next": None}),
    ]
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="user-token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="api-key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.get", side_effect=pages
        ) as get,
    ):
        assert sync.get_rebrickable_lost_parts() == [{"id": 1}, {"id": 2}]

    assert get.call_args_list[0].kwargs == {
        "headers": {"Accept": "application/json", "Authorization": "key api-key"},
        "params": {"page": 1},
        "timeout": 30,
    }


def test_add_lost_parts_uses_bulk_payload_and_reports_actual_additions():
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.post",
            return_value=response(201, [{}, {}]),
        ) as post,
    ):
        result = sync.add_lost_parts_to_rebrickable(
            [
                {"inv_part_id": 4, "missing_quantity": 2},
                {"inv_part_id": 9, "missing_quantity": 1},
            ]
        )

    assert result["success"] is True
    assert result["added"] == 2
    assert post.call_args.kwargs["json"] == [
        {"inv_part_id": 4, "lost_quantity": 2},
        {"inv_part_id": 9, "lost_quantity": 1},
    ]
    assert post.call_args.kwargs["timeout"] == 60


def test_add_lost_parts_falls_back_to_individual_requests_after_rate_limit():
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.post",
            return_value=response(429),
        ),
        patch(
            "services.rebrickable_sync_service.add_lost_parts_individually",
            return_value={"added_count": 1, "rate_limited_count": 1},
        ) as individual,
    ):
        result = sync.add_lost_parts_to_rebrickable(
            [{"inv_part_id": 4, "missing_quantity": 2}]
        )

    assert result["added"] == 1
    assert result["rate_limited_count"] == 1
    individual.assert_called_once()


def test_add_lost_parts_individually_counts_success_rate_limit_and_failure():
    with patch(
        "services.rebrickable_sync_service.requests.post",
        side_effect=[response(201), response(429), response(400, text="invalid")],
    ):
        result = sync.add_lost_parts_individually(
            [{"inv_part_id": 1}, {"inv_part_id": 2}, {"inv_part_id": 3}], {}, "token"
        )

    assert result["added"] == 1
    assert result["rate_limited_count"] == 1
    assert len(result["errors"]) == 1


def test_remove_lost_parts_uses_delete_and_retains_failed_ids():
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.delete",
            side_effect=[response(204), response(404)],
        ) as delete,
    ):
        result = sync.remove_lost_parts_from_rebrickable(
            [{"lost_part_id": 1}, {"lost_part_id": 2}, {}]
        )

    assert result["removed"] == 1
    assert result["errors"] == ["Failed to remove part 2: 404"]
    assert delete.call_count == 2


def test_part_list_lookup_create_and_pagination_contracts():
    page_one = response(200, {"results": [{"id": 1, "name": "Other"}], "next": "more"})
    page_two = response(200, {"results": [{"id": 2, "name": "Wanted"}], "next": None})
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.make_rate_limited_request",
            side_effect=[page_one, page_two],
        ),
    ):
        assert sync.get_user_part_lists() == [
            {"id": 1, "name": "Other"},
            {"id": 2, "name": "Wanted"},
        ]

    with patch(
        "services.rebrickable_sync_service.get_user_part_lists",
        return_value=[{"id": 2, "name": "Wanted"}],
    ):
        assert sync.find_or_create_missing_parts_list("Wanted") == 2

    with (
        patch("services.rebrickable_sync_service.get_user_part_lists", return_value=[]),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.post",
            return_value=response(201, {"id": 22}),
        ) as post,
    ):
        assert sync.find_or_create_missing_parts_list("Wanted") == 22
    assert post.call_args.kwargs["data"] == {
        "name": "Wanted",
        "is_buildable": False,
        "num_parts": 0,
    }


def test_part_list_add_and_individual_fallback_preserve_quantities():
    parts = [{"part_num": "3001", "color_id": 5, "missing_quantity": 3}]
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.requests.post",
            return_value=response(201, [{}]),
        ) as post,
    ):
        result = sync.add_parts_to_part_list(12, parts)
    assert result["added"] == 1
    assert post.call_args.kwargs["json"] == [
        {"part_num": "3001", "color_id": 5, "quantity": 3}
    ]

    with patch(
        "services.rebrickable_sync_service.requests.post", return_value=response(201)
    ) as post:
        assert sync.add_parts_individually_to_list(
            12,
            [{"part_num": "3001", "color_id": 5, "quantity": 3}],
            {"Accept": "application/json"},
            "token",
        ) == {"added_count": 1, "rate_limited_count": 0}
    assert post.call_args.kwargs["data"] == {
        "part_num": "3001",
        "color_id": 5,
        "quantity": 3,
    }
    assert (
        post.call_args.kwargs["headers"]["Content-Type"]
        == "application/x-www-form-urlencoded"
    )


def test_clear_part_list_recreates_list_after_successful_delete():
    with (
        patch(
            "services.rebrickable_sync_service.get_part_list_parts",
            return_value=[{"part": {}}],
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.make_rate_limited_request",
            side_effect=[response(200, {"name": "Wanted"}), response(204)],
        ),
        patch(
            "services.rebrickable_sync_service.find_or_create_missing_parts_list",
            return_value=99,
        ),
    ):
        result = sync.clear_part_list(12)
    assert result["method"] == "delete_and_recreate"
    assert result["removed"] == 1
    assert result["new_list_id"] == 99


def test_bulk_inventory_lookup_matches_only_existing_part_and_color():
    missing = [
        {"part_num": "3001", "color_id": 5, "set_num": "set-1"},
        {"part_num": "3002", "color_id": 6, "set_num": "set-1"},
        {"part_num": "unassigned", "color_id": 1, "set_num": None},
    ]
    inventory = response(
        200, {"results": [{"id": 77, "part": {"part_num": "3001"}, "color": {"id": 5}}]}
    )
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.make_rate_limited_request",
            return_value=inventory,
        ),
    ):
        assert sync.find_inventory_part_ids_bulk(missing) == [
            {"part_num": "3001", "color_id": 5, "set_num": "set-1", "inv_part_id": 77}
        ]


def test_remove_and_update_part_list_quantities_report_partial_progress():
    with (
        patch(
            "services.rebrickable_sync_service.get_rebrickable_user_token",
            return_value="token",
        ),
        patch(
            "services.rebrickable_sync_service.get_rebrickable_api_key",
            return_value="key",
        ),
        patch(
            "services.rebrickable_sync_service.make_rate_limited_request",
            return_value=response(204),
        ),
    ):
        removed = sync.remove_parts_from_part_list(
            12, [{"part_num": "3001", "color_id": 5}]
        )
    assert removed["success"] is True
    assert removed["removed"] == 1

    with (
        patch(
            "services.rebrickable_sync_service.remove_parts_from_part_list",
            return_value={"removed": 2},
        ),
        patch(
            "services.rebrickable_sync_service.add_parts_to_part_list",
            return_value={"added": 1},
        ),
    ):
        updated = sync.update_part_quantities_in_list(
            12,
            [
                {"part_num": "3001", "color_id": 5, "new_quantity": 7},
                {"part_num": "3002", "color_id": 1, "new_quantity": 1},
            ],
        )
    assert updated["success"] is True
    assert updated["updated"] == 1
    assert "rate limited" in updated["message"]


def test_missing_parts_sync_reconciles_add_remove_update_and_duplicate_quantities():
    """A sync sends only the calculated diff and sums a shared missing part."""
    local_missing = [
        {"part_num": "3001", "color_id": 5, "missing_quantity": 2, "set_num": "set-a"},
        {"part_num": "3001", "color_id": 5, "missing_quantity": 3, "set_num": "set-b"},
        {"part_num": "3002", "color_id": 1, "missing_quantity": 4, "set_num": "set-a"},
    ]
    current_parts = [
        {"id": 101, "part": {"part_num": "3001"}, "color": {"id": 5}, "quantity": 1},
        {
            "id": 102,
            "part": {"part_num": "obsolete"},
            "color": {"id": 2},
            "quantity": 1,
        },
    ]
    with (
        patch(
            "services.rebrickable_sync_service.get_local_missing_parts",
            return_value=local_missing,
        ) as local,
        patch(
            "services.rebrickable_sync_service.find_or_create_missing_parts_list",
            return_value=17,
        ),
        patch(
            "services.rebrickable_sync_service.get_part_list_parts",
            return_value=current_parts,
        ),
        patch(
            "services.rebrickable_sync_service.remove_parts_from_part_list",
            return_value={"removed": 1},
        ) as remove,
        patch(
            "services.rebrickable_sync_service.add_parts_to_part_list",
            return_value={"added": 1, "rate_limited_count": 0},
        ) as add,
        patch(
            "services.rebrickable_sync_service.update_part_quantities_in_list",
            return_value={"updated": 1},
        ) as update,
    ):
        result = sync.sync_missing_parts_with_rebrickable()

    local.assert_called_once_with(include_spare=False, include_minifig=False)
    remove.assert_called_once_with(
        17,
        [{"part_num": "obsolete", "color_id": 2, "quantity": 1, "list_part_id": 102}],
    )
    add.assert_called_once_with(
        17,
        [
            {
                "part_num": "3002",
                "color_id": 1,
                "missing_quantity": 4,
                "set_num": "set-a",
                "source_sets": ["set-a"],
            }
        ],
    )
    update.assert_called_once_with(
        17,
        [
            {
                "part_num": "3001",
                "color_id": 5,
                "old_quantity": 1,
                "new_quantity": 5,
                "list_part_id": 101,
            }
        ],
    )
    assert result["summary"] == {
        "local_missing_count": 3,
        "list_parts_count": 2,
        "to_add": 1,
        "to_remove": 1,
        "to_update": 1,
        "list_id": 17,
        "actual_added": 1,
        "actual_removed": 1,
        "actual_updated": 1,
        "rate_limited_count": 0,
        "total_local": 3,
        "sample_processed": 1,
        "message": "Smart synchronization completed! Found 3 missing parts locally vs 2 in list. Added 1 new missing parts. Removed 1 parts no longer missing. Updated quantities for 1 parts. ",
    }


def test_missing_parts_sync_returns_failure_when_list_cannot_be_created():
    with (
        patch(
            "services.rebrickable_sync_service.get_local_missing_parts", return_value=[]
        ),
        patch(
            "services.rebrickable_sync_service.find_or_create_missing_parts_list",
            return_value=None,
        ),
    ):
        result = sync.sync_missing_parts_with_rebrickable()
    assert result == {
        "success": False,
        "message": "Failed to create or find missing parts list on Rebrickable",
    }


def test_minifigure_sync_reports_no_changes_without_writes():
    """A matching minifigure list does not issue remote mutation operations."""
    matching_part = {
        "part_num": "head-1",
        "color_id": 2,
        "missing_quantity": 1,
        "minifigure_id": 8,
    }
    current_part = {
        "id": 55,
        "part": {"part_num": "head-1"},
        "color": {"id": 2},
        "quantity": 1,
    }
    with (
        patch(
            "services.rebrickable_sync_service.get_local_missing_minifigure_parts",
            return_value=[matching_part],
        ) as local,
        patch(
            "services.rebrickable_sync_service.find_or_create_missing_parts_list",
            return_value=23,
        ),
        patch(
            "services.rebrickable_sync_service.get_part_list_parts",
            return_value=[current_part],
        ),
        patch(
            "services.rebrickable_sync_service.remove_parts_from_part_list"
        ) as remove,
        patch("services.rebrickable_sync_service.add_parts_to_part_list") as add,
        patch(
            "services.rebrickable_sync_service.update_part_quantities_in_list"
        ) as update,
    ):
        result = sync.sync_missing_minifigure_parts_with_rebrickable()

    local.assert_called_once_with(include_spare=False)
    remove.assert_not_called()
    add.assert_not_called()
    update.assert_not_called()
    assert result["summary"]["message"].endswith(
        "No changes needed - minifigure lists are already in sync! "
    )


def test_minifigure_sync_reconciles_add_remove_and_update():
    local_missing = [
        {"part_num": "hand", "color_id": 1, "missing_quantity": 2, "minifigure_id": 4},
        {"part_num": "hand", "color_id": 1, "missing_quantity": 1, "minifigure_id": 5},
        {"part_num": "head", "color_id": 2, "missing_quantity": 1, "minifigure_id": 4},
    ]
    current_parts = [
        {"id": 1, "part": {"part_num": "hand"}, "color": {"id": 1}, "quantity": 2},
        {"id": 2, "part": {"part_num": "old"}, "color": {"id": 3}, "quantity": 1},
    ]
    with (
        patch(
            "services.rebrickable_sync_service.get_local_missing_minifigure_parts",
            return_value=local_missing,
        ),
        patch(
            "services.rebrickable_sync_service.find_or_create_missing_parts_list",
            return_value=23,
        ),
        patch(
            "services.rebrickable_sync_service.get_part_list_parts",
            return_value=current_parts,
        ),
        patch(
            "services.rebrickable_sync_service.remove_parts_from_part_list",
            return_value={"removed": 1},
        ) as remove,
        patch(
            "services.rebrickable_sync_service.add_parts_to_part_list",
            return_value={"added": 1, "rate_limited_count": 1},
        ) as add,
        patch(
            "services.rebrickable_sync_service.update_part_quantities_in_list",
            return_value={"updated": 1},
        ) as update,
    ):
        result = sync.sync_missing_minifigure_parts_with_rebrickable(batch_size=1)

    remove.assert_called_once()
    assert add.call_args.args[1] == [
        {
            "part_num": "head",
            "color_id": 2,
            "missing_quantity": 1,
            "minifigure_id": 4,
            "source_minifigures": [4],
        }
    ]
    update.assert_called_once_with(
        23,
        [
            {
                "part_num": "hand",
                "color_id": 1,
                "old_quantity": 2,
                "new_quantity": 3,
                "list_part_id": 1,
            }
        ],
    )
    assert result["summary"]["rate_limited_count"] == 1
    assert "rate limited" in result["summary"]["message"]
