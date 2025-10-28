"""
Admin sync routes for managing Rebrickable synchronization.
This module handles syncing missing parts and user sets with Rebrickable.
"""

import logging

from flask import Blueprint, jsonify, render_template, request
from services.rebrickable_sync_service import (
    sync_missing_minifigure_parts_with_rebrickable,
    sync_missing_parts_with_rebrickable,
)
from services.token_service import get_rebrickable_api_key, get_rebrickable_user_token

logger = logging.getLogger(__name__)

# Define the admin sync blueprint
admin_sync_bp = Blueprint("admin_sync", __name__)


@admin_sync_bp.route("/admin/sync")
def admin_sync_page():
    """
    Display the admin synchronization page.
    """
    try:
        # Check if tokens are configured
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        tokens_configured = bool(user_token and api_key)

        return render_template(
            "admin_sync.html",
            tokens_configured=tokens_configured,
            user_token_exists=bool(user_token),
            api_key_exists=bool(api_key),
        )

    except Exception as e:
        logger.error(f"Error loading admin sync page: {e}")
        return render_template(
            "admin_sync.html", tokens_configured=False, error_message=str(e)
        )


@admin_sync_bp.route("/admin/sync/check_availability")
def check_sync_availability():
    """
    Check if synchronization is available (tokens configured).
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        if user_token and api_key:
            return jsonify(
                {"available": True, "message": "Sync available - tokens configured"}
            )
        else:
            missing = []
            if not user_token:
                missing.append("User Token")
            if not api_key:
                missing.append("API Key")

            return jsonify(
                {"available": False, "message": f'Missing: {", ".join(missing)}'}
            )

    except Exception as e:
        logger.error(f"Error checking sync availability: {e}")
        return (
            jsonify(
                {
                    "available": False,
                    "message": f"Error checking availability: {str(e)}",
                }
            ),
            500,
        )


@admin_sync_bp.route("/admin/sync/missing_parts", methods=["POST"])
def sync_missing_parts():
    """
    Synchronize missing parts with Rebrickable Lost Parts.
    Accepts optional batch_size parameter to control how many parts to process.
    """
    try:
        # Check if sync is available
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        if not user_token or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Rebrickable credentials not configured. Please set up your API token first.",
                    }
                ),
                400,
            )

        # Get batch size from request data (optional)
        data = request.get_json() or {}
        batch_size = data.get("batch_size")

        # Perform the synchronization
        result = sync_missing_parts_with_rebrickable(batch_size=batch_size)

        # Enhance the response with rate limiting information if available
        if result["success"] and "summary" in result:
            summary = result["summary"]
            # Add rate limiting info from the add operation if available
            if "missing_parts_add_result" in summary:
                add_result = summary["missing_parts_add_result"]
                if "rate_limited_count" in add_result:
                    summary["rate_limited_count"] = add_result["rate_limited_count"]

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error during missing parts sync: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Missing parts synchronization failed: {str(e)}",
                }
            ),
            500,
        )


@admin_sync_bp.route("/admin/sync/missing_minifigure_parts", methods=["POST"])
def sync_missing_minifigure_parts():
    """
    Synchronize missing minifigure parts with Rebrickable Part Lists.
    Accepts optional batch_size parameter to control how many parts to process.
    """
    try:
        # Check if sync is available
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        if not user_token or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Rebrickable credentials not configured. Please set up your API token first.",
                    }
                ),
                400,
            )

        # Get batch size from request data (optional)
        data = request.get_json() or {}
        batch_size = data.get("batch_size")

        # Perform the synchronization
        result = sync_missing_minifigure_parts_with_rebrickable(batch_size=batch_size)

        # Enhance the response with rate limiting information if available
        if result["success"] and "summary" in result:
            summary = result["summary"]
            # Add rate limiting info from the add operation if available
            if "missing_parts_add_result" in summary:
                add_result = summary["missing_parts_add_result"]
                if "rate_limited_count" in add_result:
                    summary["rate_limited_count"] = add_result["rate_limited_count"]

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error during missing minifigure parts sync: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Missing minifigure parts synchronization failed: {str(e)}",
                }
            ),
            500,
        )


@admin_sync_bp.route("/admin/sync/all_missing_parts", methods=["POST"])
def sync_all_missing_parts():
    """
    Synchronize both regular and minifigure missing parts with Rebrickable Part Lists.
    This is a convenience endpoint that calls both sync functions.
    """
    try:
        # Check if sync is available
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        if not user_token or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Rebrickable credentials not configured. Please set up your API token first.",
                    }
                ),
                400,
            )

        # Get batch size from request data (optional)
        data = request.get_json() or {}
        batch_size = data.get("batch_size")

        # Perform both synchronizations
        regular_result = sync_missing_parts_with_rebrickable(batch_size=batch_size)
        minifig_result = sync_missing_minifigure_parts_with_rebrickable(
            batch_size=batch_size
        )

        # Combine results
        combined_result = {
            "success": regular_result["success"] and minifig_result["success"],
            "regular_parts": regular_result,
            "minifigure_parts": minifig_result,
            "summary": {
                "regular_local_count": regular_result.get("summary", {}).get(
                    "local_missing_count", 0
                ),
                "minifig_local_count": minifig_result.get("summary", {}).get(
                    "local_missing_count", 0
                ),
                "regular_added": regular_result.get("summary", {}).get(
                    "actual_added", 0
                ),
                "minifig_added": minifig_result.get("summary", {}).get(
                    "actual_added", 0
                ),
                "regular_removed": regular_result.get("summary", {}).get(
                    "actual_removed", 0
                ),
                "minifig_removed": minifig_result.get("summary", {}).get(
                    "actual_removed", 0
                ),
                "regular_list_id": regular_result.get("summary", {}).get("list_id"),
                "minifig_list_id": minifig_result.get("summary", {}).get("list_id"),
            },
        }

        total_local = (
            combined_result["summary"]["regular_local_count"]
            + combined_result["summary"]["minifig_local_count"]
        )
        total_added = (
            combined_result["summary"]["regular_added"]
            + combined_result["summary"]["minifig_added"]
        )
        total_removed = (
            combined_result["summary"]["regular_removed"]
            + combined_result["summary"]["minifig_removed"]
        )

        combined_result["summary"]["message"] = (
            f"Combined sync completed! Found {total_local} total missing parts "
            f"({combined_result['summary']['regular_local_count']} regular + "
            f"{combined_result['summary']['minifig_local_count']} minifigure). "
            f"Added {total_added}, removed {total_removed} parts across both lists."
        )

        if combined_result["success"]:
            return jsonify(combined_result)
        else:
            return jsonify(combined_result), 500

    except Exception as e:
        logger.error(f"Error during combined missing parts sync: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Combined missing parts synchronization failed: {str(e)}",
                }
            ),
            500,
        )


@admin_sync_bp.route("/admin/sync/user_sets", methods=["POST"])
def sync_user_sets():
    """
    Synchronize user sets with Rebrickable 'Brick_Manager' list.
    Creates the list if it doesn't exist.
    """
    try:
        # Check if sync is available
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        if not user_token or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Rebrickable credentials not configured. Please set up your API token first.",
                    }
                ),
                400,
            )

        # Import the service function (will be created next)
        from services.rebrickable_sets_sync_service import (
            sync_user_sets_with_rebrickable,
        )

        # Perform the synchronization
        result = sync_user_sets_with_rebrickable()

        # Enhance the response with rate limiting information if available
        if result["success"] and "summary" in result:
            summary = result["summary"]
            # Add rate limiting info from the add operation if available
            if "sets_to_add_result" in summary:
                add_result = summary["sets_to_add_result"]
                if "rate_limited_count" in add_result:
                    summary["rate_limited_count"] = add_result["rate_limited_count"]
                if "added_count" in add_result:
                    summary["sets_added"] = add_result["added_count"]

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error during user sets sync: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"User sets synchronization failed: {str(e)}",
                }
            ),
            500,
        )
