"""Route for synchronizing missing parts with Rebrickable Lost Parts."""

import logging

from flask import Blueprint, jsonify, request
from services.rebrickable_sync_service import sync_missing_parts_with_rebrickable
from services.token_service import get_rebrickable_api_key, get_rebrickable_user_token

logger = logging.getLogger(__name__)

rebrickable_sync_bp = Blueprint("rebrickable_sync", __name__)


@rebrickable_sync_bp.route("/check_sync_availability", methods=["GET"])
def check_sync_availability():
    """Check if Rebrickable sync is available (user token exists)."""
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()

        available = bool(user_token and api_key)

        return jsonify(
            {
                "available": available,
                "message": "Rebrickable sync is available"
                if available
                else "Missing Rebrickable credentials",
            }
        )

    except Exception as e:
        logger.error(f"Error checking sync availability: {e}")
        return (
            jsonify({"available": False, "message": "Error checking availability"}),
            500,
        )


@rebrickable_sync_bp.route("/sync_missing_parts", methods=["POST"])
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
        _result = sync_missing_parts_with_rebrickable(batch_size=batch_size)

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Error during sync: {e}")
        return (
            jsonify({"success": False, "message": f"Synchronization failed: {str(e)}"}),
            500,
        )
